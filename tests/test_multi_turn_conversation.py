import sys
import os
import time
import json
import unittest
from pathlib import Path

# Fix terminal encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.orchestrator import LegalAgentOrchestrator, ChatbotResult
from src.agents.intent_agent import IntentAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.legal_analysis_agent import LegalAnalysisAgent, LegalAnalysisResult, LegalCitation
from src.agents.validation_agent import ValidationAgent
from src.agents.response_agent import ResponseAgent
from src.memory.conversation_memory import SessionManager, ConversationMemory
from src.memory.query_rewriter import ContextAwareQueryRewriter

class FastMockAnalysisAgent:
    """
    Lightweight analysis stub for high-speed multi-turn orchestration testing.
    Extracts citations directly from retrieved chunks to avoid 20s CPU LLM inference per turn.
    """
    def __init__(self):
        pass

    def analyze(self, query: str, retrieval) -> LegalAnalysisResult:
        citations = []
        if retrieval and retrieval.all_chunks:
            top_c = retrieval.all_chunks[0]
            citations.append(LegalCitation(
                document_name=top_c.document_name,
                document_number=top_c.document_number,
                article=top_c.article,
                clause=top_c.clause,
                page_start=top_c.page_start,
                chunk_id=top_c.chunk_id
            ))
        return LegalAnalysisResult(
            status="success",
            is_sufficient=True,
            conclusion=f"Căn cứ quy định pháp luật tương ứng cho: {query[:80]}.",
            legal_citations=citations,
            conditions=["Áp dụng theo quy định hiện hành"],
            rates_and_deadlines=["Theo quy định"],
            exceptions=[],
            raw_llm_response="Phân tích nội bộ giả định cho kiểm thử hội thoại đa lượt.",
            completion_tokens=60,
            inference_time_sec=0.01
        )


class TestMultiTurnScenarios(unittest.TestCase):
    """
    Comprehensive verification for 10 Multi-turn Conversation Scenarios (MT01 to MT10).
    Verifies:
    - State before and after each turn
    - Topic identification & preservation
    - Query rewriting precision
    - Fact retention & updates
    - Session isolation
    - Clarity / Ambiguity handling
    - Sliding window memory in long dialogues
    """

    @classmethod
    def setUpClass(cls):
        cls.session_mgr = SessionManager()
        cls.session_mgr.reset_all()

        # Check if full real LLM inference is requested
        use_full_llm = os.environ.get("FULL_LLM") == "1"
        if use_full_llm:
            analysis_agent = LegalAnalysisAgent()
        else:
            analysis_agent = FastMockAnalysisAgent()

        cls.orchestrator = LegalAgentOrchestrator(
            analysis_agent=analysis_agent,
            session_manager=cls.session_mgr
        )
        cls.results_log = []

    def setUp(self):
        # Fresh unique session for each test method
        self.session_id = f"test_{self._testMethodName}_{int(time.time()*1000)}"

    def test_MT01_overtime_salary_follow_up(self):
        """MT01: Hỏi lương làm thêm cuối tuần -> hỏi lương 30 triệu thì sao -> Giữ chủ đề làm thêm."""
        # Turn 1
        q1 = "Lương làm thêm cuối tuần là bao nhiêu?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)

        self.assertEqual(mem.state.current_topic, "tien_luong_lam_them_gio")
        self.assertFalse(r1.is_follow_up)

        # Turn 2: Follow-up adding salary
        q2 = "Lương của tôi là 30 triệu thì sao?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertTrue(r2.is_follow_up)
        self.assertIsNotNone(r2.rewritten_query)
        self.assertIn("30 triệu", r2.rewritten_query)
        self.assertIn("Điều 98", r2.rewritten_query)
        self.assertIn("ngày nghỉ hằng tuần", r2.rewritten_query)
        self.assertEqual(mem.state.current_topic, "tien_luong_lam_them_gio")
        self.assertEqual(mem.state.user_provided_facts.get("salary"), "30 triệu đồng")

        self.results_log.append({
            "scenario": "MT01",
            "name": "Lương làm thêm -> Thêm mức lương 30 triệu",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "rewritten": r2.rewritten_query,
            "active_topic": mem.state.current_topic,
            "facts": mem.state.user_provided_facts
        })

    def test_MT02_annual_leave_seniority_follow_up(self):
        """MT02: Hỏi nghỉ phép năm -> hỏi làm 5 năm thì sao -> Giữ chủ đề nghỉ phép và thâm niên."""
        # Turn 1
        q1 = "Người lao động được nghỉ phép năm bao nhiêu ngày?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)

        self.assertEqual(mem.state.current_topic, "nghi_phep_hang_nam")

        # Turn 2: Follow-up adding 5 years seniority
        q2 = "Nếu làm việc 5 năm thì sao?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertTrue(r2.is_follow_up)
        self.assertIsNotNone(r2.rewritten_query)
        self.assertIn("5 năm", r2.rewritten_query)
        self.assertIn("Điều 113", r2.rewritten_query)
        self.assertEqual(mem.state.current_topic, "nghi_phep_hang_nam")
        self.assertEqual(mem.state.user_provided_facts.get("seniority"), "5 năm")

        self.results_log.append({
            "scenario": "MT02",
            "name": "Nghỉ phép năm -> Thêm thâm niên 5 năm",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "rewritten": r2.rewritten_query,
            "active_topic": mem.state.current_topic,
            "facts": mem.state.user_provided_facts
        })

    def test_MT03_maternity_duration_follow_up(self):
        """MT03: Hỏi điều kiện thai sản -> hỏi cần đóng BHXH bao lâu -> Giữ chủ đề thai sản."""
        # Turn 1
        q1 = "Điều kiện hưởng chế độ thai sản là gì?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)

        self.assertEqual(mem.state.current_topic, "che_do_thai_san")

        # Turn 2: Follow-up asking insurance duration
        q2 = "Vậy cần đóng bảo hiểm bao lâu?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertTrue(r2.is_follow_up)
        self.assertIsNotNone(r2.rewritten_query)
        self.assertIn("chế độ thai sản", r2.rewritten_query)
        self.assertIn("thời gian đóng bảo hiểm xã hội", r2.rewritten_query.lower())
        self.assertEqual(mem.state.current_topic, "che_do_thai_san")

        self.results_log.append({
            "scenario": "MT03",
            "name": "Điều kiện thai sản -> Thời gian đóng BHXH",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "rewritten": r2.rewritten_query,
            "active_topic": mem.state.current_topic
        })

    def test_MT04_contract_termination_notice_period(self):
        """MT04: Hỏi đơn phương chấm dứt HĐLĐ -> hỏi báo trước bao nhiêu ngày -> Giữ chủ đề NSDLĐ chấm dứt."""
        # Turn 1
        q1 = "Người sử dụng lao động có được đơn phương chấm dứt hợp đồng không?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)

        self.assertEqual(mem.state.current_topic, "cham_dut_hop_dong_lao_dong")

        # Turn 2: Follow-up asking notice period
        q2 = "Còn phải báo trước bao nhiêu ngày?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertTrue(r2.is_follow_up)
        self.assertIsNotNone(r2.rewritten_query)
        self.assertIn("người sử dụng lao động", r2.rewritten_query.lower())
        self.assertIn("báo trước", r2.rewritten_query.lower())
        self.assertIn("Điều 36", r2.rewritten_query)
        self.assertEqual(mem.state.current_topic, "cham_dut_hop_dong_lao_dong")

        self.results_log.append({
            "scenario": "MT04",
            "name": "Đơn phương chấm dứt HĐLĐ -> Thời hạn báo trước",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "rewritten": r2.rewritten_query,
            "active_topic": mem.state.current_topic
        })

    def test_MT05_topic_shift_handling(self):
        """MT05: Hỏi lương làm thêm -> chuyển sang hỏi điều kiện hưởng thai sản -> Nhận diện chủ đề mới, làm sạch ngữ cảnh cũ."""
        # Turn 1
        q1 = "Lương làm thêm cuối tuần là bao nhiêu?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)
        mem.update_facts({"salary": "30 triệu"})

        self.assertEqual(mem.state.current_topic, "tien_luong_lam_them_gio")

        # Turn 2: Topic shift to maternity
        q2 = "Điều kiện hưởng chế độ thai sản là gì?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertFalse(r2.is_follow_up)
        self.assertEqual(mem.state.current_topic, "che_do_thai_san")
        # Ensure overtime salary fact was cleared from active state
        self.assertNotIn("salary", mem.state.user_provided_facts)
        # Ensure response doesn't mention overtime salary
        self.assertNotIn("Điều 98", r2.intent.normalized_query)

        self.results_log.append({
            "scenario": "MT05",
            "name": "Chuyển chủ đề từ Làm thêm sang Thai sản",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "new_topic": mem.state.current_topic,
            "facts_cleared": "salary" not in mem.state.user_provided_facts
        })

    def test_MT06_fact_correction_sequence(self):
        """MT06: Hỏi lương làm thêm -> bổ sung lương 20 triệu -> sửa lại lương 25 triệu -> Cập nhật đúng dữ kiện mới."""
        # Turn 1
        q1 = "Lương làm thêm cuối tuần là bao nhiêu?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)

        # Turn 2: Add 20 million
        q2 = "Lương của tôi là 20 triệu thì sao?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)
        mem = self.session_mgr.get_or_create_memory(self.session_id)
        self.assertEqual(mem.state.user_provided_facts.get("salary"), "20 triệu đồng")

        # Turn 3: User corrects to 25 million
        q3 = "À không, lương của tôi là 25 triệu thì sao?"
        r3 = self.orchestrator.process_query(q3, session_id=self.session_id)

        self.assertTrue(r3.is_follow_up)
        self.assertEqual(mem.state.user_provided_facts.get("salary"), "25 triệu đồng")
        self.assertIn("25 triệu", r3.rewritten_query)

        self.results_log.append({
            "scenario": "MT06",
            "name": "Bổ sung dữ kiện và đính chính (20tr -> 25tr)",
            "passed": True,
            "q2_salary": "20 triệu đồng",
            "q3_corrected_salary": mem.state.user_provided_facts.get("salary"),
            "rewritten_turn3": r3.rewritten_query
        })

    def test_MT07_multi_session_isolation(self):
        """MT07: Hai session hỏi hai chủ đề khác nhau -> Không rò rỉ ngữ cảnh giữa các session."""
        session_A = f"sess_A_{int(time.time()*1000)}"
        session_B = f"sess_B_{int(time.time()*1000)}"

        # Session A asks about annual leave and gives 5 years seniority
        self.orchestrator.process_query("Người lao động được nghỉ phép năm bao nhiêu ngày?", session_id=session_A)
        self.orchestrator.process_query("Nếu làm việc 5 năm thì sao?", session_id=session_A)

        # Session B asks about maternity
        self.orchestrator.process_query("Điều kiện hưởng chế độ thai sản là gì?", session_id=session_B)
        r_b2 = self.orchestrator.process_query("Vậy cần đóng bảo hiểm bao lâu?", session_id=session_B)

        mem_a = self.session_mgr.get_or_create_memory(session_A)
        mem_b = self.session_mgr.get_or_create_memory(session_B)

        # Verify A has annual leave, seniority 5 years, NO maternity
        self.assertEqual(mem_a.state.current_topic, "nghi_phep_hang_nam")
        self.assertEqual(mem_a.state.user_provided_facts.get("seniority"), "5 năm")
        self.assertNotIn("thai sản", str(mem_a.state.legal_documents))

        # Verify B has maternity, NO seniority 5 years
        self.assertEqual(mem_b.state.current_topic, "che_do_thai_san")
        self.assertNotIn("seniority", mem_b.state.user_provided_facts)
        self.assertNotIn("5 năm", r_b2.rewritten_query or "")

        self.results_log.append({
            "scenario": "MT07",
            "name": "Cô lập dữ liệu giữa 2 session đồng thời",
            "passed": True,
            "session_A_topic": mem_a.state.current_topic,
            "session_A_facts": mem_a.state.user_provided_facts,
            "session_B_topic": mem_b.state.current_topic,
            "session_B_facts": mem_b.state.user_provided_facts
        })

    def test_MT08_independent_query_untouched(self):
        """MT08: Câu hỏi độc lập, đầy đủ -> Không bị viết lại sai."""
        # Turn 1
        q1 = "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)

        # Turn 2: Completely independent question
        q2 = "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        self.assertFalse(r2.is_follow_up)
        self.assertFalse(r2.is_rewritten)
        self.assertEqual(r2.question, q2)
        # Ensure ốm đau is not injected into thử việc
        self.assertNotIn("ốm đau", r2.intent.normalized_query)

        self.results_log.append({
            "scenario": "MT08",
            "name": "Câu hỏi độc lập không bị viết lại",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "is_rewritten": r2.is_rewritten
        })

    def test_MT09_ambiguous_query_clarification(self):
        """MT09: Câu hỏi có nhiều cách hiểu / mơ hồ -> Biết yêu cầu làm rõ."""
        # Turn 1
        q1 = "Lương làm thêm giờ ngày thường và ngày nghỉ hàng tuần tính như thế nào?"
        r1 = self.orchestrator.process_query(q1, session_id=self.session_id)

        # Turn 2: Ambiguous query
        q2 = "còn cái kia thì sao?"
        r2 = self.orchestrator.process_query(q2, session_id=self.session_id)

        # Expect clarification triggered
        self.assertIn("LÀM RÕ", r2.response.formatted_markdown)
        self.assertFalse(r2.response.is_answerable)

        self.results_log.append({
            "scenario": "MT09",
            "name": "Xử lý câu hỏi mơ hồ yêu cầu làm rõ",
            "passed": True,
            "q1": q1,
            "q2": q2,
            "clarification_requested": not r2.response.is_answerable
        })

    def test_MT10_long_dialogue_sliding_window(self):
        """MT10: Hội thoại dài nhiều lượt -> Giữ được thông tin quan trọng mà không làm tràn context."""
        mem = self.session_mgr.get_or_create_memory(self.session_id, max_turns=5)

        queries = [
            "Lương làm thêm cuối tuần là bao nhiêu?",
            "Lương của tôi là 30 triệu thì sao?",
            "Nếu làm thêm vào ban đêm thì tính thế nào?",
            "Làm thêm vào ngày nghỉ lễ thì sao?",
            "Có được nghỉ bù không?",
            "Cách tính tổng tiền làm thêm tháng này thế nào?",
            "Doanh nghiệp không trả tiền làm thêm thì bị phạt bao nhiêu?"
        ]

        for idx, q in enumerate(queries, 1):
            r = self.orchestrator.process_query(q, session_id=self.session_id)
            self.assertIsNotNone(r.response)

        # History should be bounded by max_turns = 5
        self.assertLessEqual(len(mem.history), 5)
        # Latest queries are in history
        self.assertEqual(mem.history[-1].user_query, queries[-1])

        self.results_log.append({
            "scenario": "MT10",
            "name": "Hội thoại dài nhiều lượt (7 turns, sliding window 5)",
            "passed": True,
            "total_turns": len(queries),
            "retained_history_turns": len(mem.history),
            "max_turns_limit": mem.max_turns
        })

    @classmethod
    def tearDownClass(cls):
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / "audit_multi_turn_scenarios.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "audit_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_scenarios": len(cls.results_log),
                "passed_scenarios": sum(1 for r in cls.results_log if r["passed"]),
                "scenarios": cls.results_log
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[Multi-Turn Suite] Đã lưu báo cáo kiểm thử tại: {report_file}")


if __name__ == "__main__":
    unittest.main()
