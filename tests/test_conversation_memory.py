import sys
import unittest
from pathlib import Path

# Fix terminal encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.memory.conversation_memory import (
    TurnRecord,
    ConversationState,
    ConversationMemory,
    SessionManager
)
from src.memory.query_rewriter import ContextAwareQueryRewriter, RewriteResult

class TestConversationMemoryUnit(unittest.TestCase):
    """
    Unit test suite for ConversationMemory, ConversationState, and SessionManager.
    """

    def setUp(self):
        self.session_mgr = SessionManager()
        self.session_mgr.reset_all()

    def test_memory_creation_and_add_turn(self):
        mem = self.session_mgr.get_or_create_memory("test_s1", max_turns=4)
        self.assertEqual(mem.session_id, "test_s1")
        self.assertEqual(len(mem.history), 0)

        # Add turn 1
        turn1 = mem.add_turn(
            user_query="Lương làm thêm cuối tuần là bao nhiêu?",
            rewritten_query=None,
            bot_response="Mức lương làm thêm vào ngày nghỉ hằng tuần tối thiểu là 200%.",
            intent_domain="labor_law",
            legal_documents=["Bộ luật Lao động 2019"],
            legal_articles=["Điều 98"],
            extracted_facts={"day_type": "ngày nghỉ hằng tuần"}
        )
        self.assertEqual(turn1.turn_id, 1)
        self.assertEqual(mem.state.turn_count, 1)
        self.assertEqual(mem.state.last_query, "Lương làm thêm cuối tuần là bao nhiêu?")
        self.assertIn("Điều 98", mem.state.legal_articles)
        self.assertEqual(mem.state.user_provided_facts.get("day_type"), "ngày nghỉ hằng tuần")

    def test_sliding_window_limit(self):
        """Ensures oldest turns are smoothly dropped when exceeding max_turns."""
        mem = self.session_mgr.get_or_create_memory("test_window", max_turns=3)
        for i in range(1, 6):
            mem.add_turn(
                user_query=f"Câu hỏi số {i}",
                rewritten_query=None,
                bot_response=f"Trả lời số {i}"
            )
        # Should only retain last 3 turns
        self.assertEqual(len(mem.history), 3)
        self.assertEqual(mem.history[0].user_query, "Câu hỏi số 3")
        self.assertEqual(mem.history[-1].user_query, "Câu hỏi số 5")

    def test_fact_update_and_overwrite(self):
        """Ensures facts are updated and overwritten on correction (MT06 logic)."""
        mem = self.session_mgr.get_or_create_memory("test_facts")
        mem.update_facts({"salary": "20 triệu", "actor": "người lao động"})
        self.assertEqual(mem.state.user_provided_facts["salary"], "20 triệu")
        self.assertEqual(mem.state.user_provided_facts["actor"], "người lao động")

        # Overwrite salary
        mem.update_facts({"salary": "25 triệu"})
        self.assertEqual(mem.state.user_provided_facts["salary"], "25 triệu")
        self.assertEqual(mem.state.user_provided_facts["actor"], "người lao động")

    def test_topic_transition_and_clear_facts(self):
        """Ensures topic shift clears stale topic-specific facts without corrupting session."""
        mem = self.session_mgr.get_or_create_memory("test_shift")
        mem.set_topic("tien_luong_lam_them_gio", "Tiền lương làm thêm", docs=["BLLĐ 2019"], articles=["Điều 98"])
        mem.update_facts({"salary": "30 triệu", "day_type": "ngày nghỉ hằng tuần"})

        # Shift to maternity
        mem.set_topic(
            "che_do_thai_san",
            "Chế độ thai sản",
            docs=["Luật BHXH 2024"],
            articles=["Điều 50"],
            clear_old_facts=True
        )
        self.assertEqual(mem.state.current_topic, "che_do_thai_san")
        self.assertEqual(len(mem.state.user_provided_facts), 0)
        self.assertIn("Điều 50", mem.state.legal_articles)
        self.assertNotIn("Điều 98", mem.state.legal_articles)

    def test_session_isolation(self):
        """Ensures distinct sessions do not leak data to each other (MT07 logic)."""
        mem_a = self.session_mgr.get_or_create_memory("session_A")
        mem_b = self.session_mgr.get_or_create_memory("session_B")

        mem_a.set_topic("tien_luong_lam_them_gio")
        mem_a.update_facts({"salary": "50 triệu"})

        mem_b.set_topic("che_do_thai_san")
        mem_b.update_facts({"child_count": 1})

        # Check A
        self.assertEqual(mem_a.state.current_topic, "tien_luong_lam_them_gio")
        self.assertEqual(mem_a.state.user_provided_facts.get("salary"), "50 triệu")
        self.assertNotIn("child_count", mem_a.state.user_provided_facts)

        # Check B
        self.assertEqual(mem_b.state.current_topic, "che_do_thai_san")
        self.assertEqual(mem_b.state.user_provided_facts.get("child_count"), 1)
        self.assertNotIn("salary", mem_b.state.user_provided_facts)


class TestQueryRewriterUnit(unittest.TestCase):
    """
    Unit test suite for ContextAwareQueryRewriter.
    """

    def setUp(self):
        self.rewriter = ContextAwareQueryRewriter()
        self.session_mgr = SessionManager()
        self.session_mgr.reset_all()

    def test_entity_extraction(self):
        q1 = "Lương của tôi là 30 triệu thì sao?"
        e1 = self.rewriter.extract_entities(q1)
        self.assertEqual(e1.get("salary"), "30 triệu đồng")

        q2 = "Nếu làm việc 5 năm thì sao?"
        e2 = self.rewriter.extract_entities(q2)
        self.assertEqual(e2.get("seniority"), "5 năm")

        q3 = "Người sử dụng lao động đơn phương chấm dứt hợp đồng"
        e3 = self.rewriter.extract_entities(q3)
        self.assertEqual(e3.get("actor"), "người sử dụng lao động")

    def test_independent_query_not_rewritten(self):
        """MT08: Independent complete query must remain untouched."""
        mem = self.session_mgr.get_or_create_memory("s_indep")
        mem.set_topic("tien_luong_lam_them_gio")

        query = "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?"
        res = self.rewriter.rewrite_query(query, mem)
        self.assertFalse(res.is_follow_up)
        self.assertFalse(res.is_rewritten)
        self.assertEqual(res.rewritten_query, query)

    def test_ambiguous_query_flags_clarification(self):
        """MT09: Ambiguous query triggers needs_clarification."""
        mem = self.session_mgr.get_or_create_memory("s_ambig")
        mem.set_topic("tien_luong_lam_them_gio", "Tiền lương làm thêm giờ")

        query = "còn cái kia thì sao?"
        res = self.rewriter.rewrite_query(query, mem)
        self.assertTrue(res.needs_clarification)
        self.assertIsNotNone(res.clarification_prompt)

    def test_topic_shift_detection(self):
        """MT05: Topic shift is detected and old context is not applied."""
        mem = self.session_mgr.get_or_create_memory("s_shift")
        mem.set_topic("tien_luong_lam_them_gio", "Tiền lương làm thêm", articles=["Điều 98"])
        mem.update_facts({"salary": "30 triệu"})

        query = "Điều kiện hưởng chế độ thai sản là gì?"
        res = self.rewriter.rewrite_query(query, mem)
        self.assertFalse(res.is_follow_up)
        self.assertTrue(res.topic_shift_detected)
        self.assertEqual(res.detected_topic, "che_do_thai_san")
        # Ensure memory topic updated to che_do_thai_san and old facts cleared
        self.assertEqual(mem.state.current_topic, "che_do_thai_san")
        self.assertNotIn("salary", mem.state.user_provided_facts)


if __name__ == "__main__":
    unittest.main()
