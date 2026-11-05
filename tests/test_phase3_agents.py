import sys
import json
import time
from pathlib import Path

# Fix terminal encoding on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.orchestrator import LegalAgentOrchestrator, ChatbotResult

TEST_QUESTIONS = [
    {
        "id": "TC01",
        "category": "Lao động - Thử việc",
        "question": "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?",
        "expected_answer_keywords": ["60 ngày", "Điều 25"]
    },
    {
        "id": "TC02",
        "category": "Lao động - Nghỉ phép",
        "question": "Người lao động được nghỉ phép hàng năm bao nhiêu ngày trong điều kiện bình thường?",
        "expected_answer_keywords": ["12 ngày", "Điều 113"]
    },
    {
        "id": "TC03",
        "category": "Lao động - Thời giờ làm việc",
        "question": "Thời giờ làm việc bình thường không quá bao nhiêu giờ trong một ngày và một tuần?",
        "expected_answer_keywords": ["8 giờ", "48 giờ", "Điều 105"]
    },
    {
        "id": "TC04",
        "category": "Lao động - Tiền lương làm thêm",
        "question": "Làm thêm giờ vào ngày nghỉ hàng tuần được trả lương tính như thế nào?",
        "expected_answer_keywords": ["200%", "Điều 98"]
    },
    {
        "id": "TC05",
        "category": "Lao động - Tiền lương ngừng việc",
        "question": "Người sử dụng lao động có phải trả lương khi người lao động phải ngừng việc do lỗi của người sử dụng lao động không?",
        "expected_answer_keywords": ["trả đủ tiền lương", "Điều 99"]
    },
    {
        "id": "TC06",
        "category": "Lao động - Đơn phương chấm dứt HĐLĐ",
        "question": "Trường hợp nào người sử dụng lao động không được thực hiện quyền đơn phương chấm dứt hợp đồng lao động?",
        "expected_answer_keywords": ["ốm đau", "Điều 37"]
    },
    {
        "id": "TC07",
        "category": "Lao động - Trách nhiệm chấm dứt HĐLĐ",
        "question": "Trách nhiệm của người sử dụng lao động khi chấm dứt hợp đồng lao động gồm những gì?",
        "expected_answer_keywords": ["14 ngày", "sổ bảo hiểm xã hội", "Điều 48"]
    },
    {
        "id": "TC08",
        "category": "BHXH - Chế độ ốm đau (Q14 Benchmark)",
        "question": "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?",
        "expected_answer_keywords": ["75%", "Điều 45", "Khoản 2"]
    },
    {
        "id": "TC09",
        "category": "BHXH - Chế độ thai sản",
        "question": "Thời gian nghỉ việc hưởng chế độ thai sản khi sinh một con là bao nhiêu tháng?",
        "expected_answer_keywords": ["06 tháng", "6 tháng", "Điều 53"]
    },
    {
        "id": "TC10",
        "category": "Ngoài phạm vi (Out of Scope)",
        "question": "Mức phạt vượt đèn đỏ đối với xe máy theo luật giao thông là bao nhiêu tiền?",
        "expected_answer_keywords": ["ngoài phạm vi"]
    }
]

def run_test_suite():
    print("="*92)
    print("CHẠY BỘ KIỂM THỬ GIAI ĐOẠN 3: AGENTIC AI LEGAL CHATBOT (10 CÂU HỎI TIÊU BIỂU)")
    print("="*92)

    orchestrator = LegalAgentOrchestrator()
    results = []

    for idx, tc in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{idx:02d}/10] {tc['id']} - {tc['category']}")
        print(f"      Câu hỏi: \"{tc['question']}\"")

        res = orchestrator.process_query(tc["question"])

        # Quick validation check
        domain_ok = res.intent.domain != "out_of_scope" if tc["id"] != "TC10" else not res.intent.is_in_scope
        val_status = res.validation.validation_status if res.validation else "N/A (OOS)"

        print(f"      => Intent: {res.intent.domain} | Validation: {val_status} | Time: {res.timing.total_time:.2f}s | ProcRAM: {res.resources.process_ram_after_mb:.1f}MB | SysRAM: {res.resources.system_ram_used_gb:.2f}GB")
        print(f"      => Kết luận: {res.response.conclusion[:100]}...")

        results.append({
            "test_id": tc["id"],
            "category": tc["category"],
            "question": tc["question"],
            "intent_domain": res.intent.domain,
            "is_in_scope": res.intent.is_in_scope,
            "retrieval_chunks_count": res.retrieval.total_retrieved if res.retrieval else 0,
            "analysis_status": res.analysis.status if res.analysis else "N/A",
            "validation_status": val_status,
            "conclusion": res.response.conclusion,
            "legal_basis": [b["document"] + " | " + b["article"] + " | " + b["clause"] for b in res.response.legal_basis],
            "timings": res.timing.to_dict(),
            "resources": res.resources.to_dict()
        })

    # Save summary report
    out_path = ROOT_DIR / "tests" / "test_results_phase3.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "="*92)
    print("BÁO CÁO TỔNG KẾT BỘ KIỂM THỬ:")
    print("="*92)
    print(f"  * Tổng số câu đã kiểm thử: {len(results)}")
    avg_time = sum(r["timings"]["total_time"] for r in results) / len(results)
    print(f"  * Thời gian xử lý trung bình: {avg_time:.2f}s/câu")
    print(f"  * Đã lưu kết quả chi tiết vào: {out_path}")

if __name__ == "__main__":
    run_test_suite()
