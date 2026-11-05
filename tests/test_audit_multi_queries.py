import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.orchestrator import LegalAgentOrchestrator

def test_multi_consecutive_queries():
    print("="*90)
    print("KIỂM TRA CHUỖI CÂU HỎI LIÊN TIẾP (MULTI-TURN & SPECIAL CASES)")
    print("="*90)

    orchestrator = LegalAgentOrchestrator()

    test_cases = [
        {
            "type": "CÂU HỎI CHUẨN (IN-SCOPE Q14)",
            "query": "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
        },
        {
            "type": "CÂU HỎI NGOÀI PHẠM VI (OUT OF SCOPE)",
            "query": "Hướng dẫn công thức nấu phở bò gia truyền Hà Nội ngon nhất?"
        },
        {
            "type": "CÂU HỎI THIẾU CĂN CỨ (INSUFFICIENT DATA)",
            "query": "Hệ số lương và phụ cấp trách nhiệm của Thẩm phán Tòa án nhân dân tối cao được tính thế nào?"
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n--- [LẦN HỎI {idx}: {tc['type']}] ---")
        print(f"Câu hỏi: \"{tc['query']}\"")

        res = orchestrator.process_query(tc["query"])

        print(f"1. Intent Agent:     Domain={res.intent.domain}, InScope={res.intent.is_in_scope} ({res.timing.intent_time*1000:.1f}ms)")
        if res.retrieval:
            print(f"2. Retrieval Agent:  {res.retrieval.total_retrieved} chunks ({res.timing.retrieval_time:.2f}s)")
        else:
            print(f"2. Retrieval Agent:  Bỏ qua (Do ngoài phạm vi)")

        if res.analysis:
            print(f"3. Analysis Agent:   Status={res.analysis.status}, Tokens={res.analysis.completion_tokens} ({res.timing.analysis_time:.2f}s)")
        else:
            print(f"3. Analysis Agent:   Bỏ qua")

        if res.validation:
            print(f"4. Validation Agent: Status={res.validation.validation_status}, PassedChecks={len(res.validation.passed_checks)}")
            for pc in res.validation.passed_checks[:2]:
                print(f"     [PASS] {pc}")
            for wm in res.validation.warning_messages:
                print(f"     [WARN] {wm}")
        else:
            print(f"4. Validation Agent: Bỏ qua")

        print(f"5. Response Agent:   IsAnswerable={res.response.is_answerable}, Confidence={res.response.confidence_level}")
        print(f"   * Kết luận:       {res.response.conclusion[:120]}...")
        print(f"6. Hiệu năng & RAM:  TotalTime={res.timing.total_time:.2f}s | ProcessRAM={res.resources.process_ram_after_mb:.1f}MB | SystemRAM={res.resources.system_ram_used_gb:.2f}GB ({res.resources.system_ram_percent}%)")

if __name__ == "__main__":
    test_multi_consecutive_queries()
