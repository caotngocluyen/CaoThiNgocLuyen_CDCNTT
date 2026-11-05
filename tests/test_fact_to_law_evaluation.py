import sys
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil
from src.agents.orchestrator import LegalAgentOrchestrator
from src.utils.logger import get_logger

logger = get_logger("TestFactToLaw")

FACT_TO_LAW_SCENARIOS = [
    {
        "id": "FTL_01",
        "category": "Nhiều điều kiện & Ngoại lệ (Điều 35 Khoản 2)",
        "question": "Công ty nợ lương 2 tháng và tự ý chuyển tôi sang làm công việc khác thỏa thuận, tôi có được nghỉ việc ngay không?",
        "expected_facts": ["người lao động", "công ty", "nợ lương", "chuyển công việc"],
        "expected_issues": ["Quyền thực hiện", "đơn phương chấm dứt"],
        "expected_article": "Điều 35",
        "expected_clause": "Khoản 2",
        "expected_conclusion_keywords": ["được quyền", "ngay", "không cần báo trước"],
        "expected_exception_keywords": ["ngoại lệ", "trừ trường hợp", "Điều 29"]
    },
    {
        "id": "FTL_02",
        "category": "Thiếu dữ kiện trọng yếu (Thử việc và BHXH)",
        "question": "Tôi đang trong thời gian thử việc thì công ty có phải đóng bảo hiểm xã hội bắt buộc không?",
        "expected_facts": ["thử việc", "bảo hiểm xã hội"],
        "expected_issues": ["Trách nhiệm", "nghĩa vụ"],
        "expected_missing_facts_keywords": ["hình thức", "hợp đồng thử việc", "hợp đồng lao động"],
        "expected_conclusion_keywords": ["tùy thuộc", "nếu", "hợp đồng lao động"]
    },
    {
        "id": "FTL_03",
        "category": "Phân tầng tỷ lệ & Điều kiện (Điều 45 Luật BHXH 2024)",
        "question": "Tôi bị ốm thông thường nghỉ việc 5 ngày thì mức hưởng trợ cấp là bao nhiêu phần trăm lương? Có được hưởng 65% không?",
        "expected_facts": ["ốm", "nghỉ việc", "5 ngày", "65%"],
        "expected_issues": ["Mức hưởng", "tỷ lệ"],
        "expected_article": "Điều 45",
        "expected_clause": "Khoản 2",
        "expected_conclusion_keywords": ["75%", "không được 65%"],
        "expected_exception_keywords": ["dài ngày", "30 năm"]
    },
    {
        "id": "FTL_04",
        "category": "Thời điểm hiệu lực pháp luật (Luật BHXH 2024)",
        "question": "Từ tháng 8/2025 tôi sinh con thì thời gian nghỉ thai sản là bao nhiêu tháng và tính theo quy định nào?",
        "expected_facts": ["sinh con", "thai sản", "tháng 8/2025"],
        "expected_issues": ["Thời hạn", "thời gian hưởng"],
        "expected_article": "Điều 53",
        "expected_temporal_keywords": ["01/07/2025", "41/2024/QH15", "hiệu lực"]
    },
    {
        "id": "FTL_05",
        "category": "Ngoài vùng phủ Knowledge Base (Luật Việc làm)",
        "question": "Tôi nghỉ việc thì bảo hiểm thất nghiệp chi trả bao nhiêu tháng lương?",
        "expected_facts": ["thất nghiệp", "nghỉ việc"],
        "expected_issues": ["Mức hưởng", "trợ cấp thất nghiệp"],
        "expected_insufficient_handling": True
    }
]

def run_evaluation():
    proc = psutil.Process(os.getpid())
    ram_start = proc.memory_info().rss / (1024 * 1024)

    print("=" * 100)
    print("KIỂM THỬ ĐÁNH GIÁ FACT-TO-LAW REASONING (PHASE 4.3)")
    print("=" * 100)

    orchestrator = LegalAgentOrchestrator()

    results = []
    total_time = 0.0

    for sc in FACT_TO_LAW_SCENARIOS:
        sc_id = sc["id"]
        cat = sc["category"]
        q = sc["question"]

        print(f"\n" + "-" * 90)
        print(f"[{sc_id}] Kịch bản: {cat}")
        print(f"Câu hỏi: '{q}'")

        t0 = time.time()
        res = orchestrator.process_query(q, session_id=f"session_{sc_id}")
        lat = time.time() - t0
        total_time += lat

        analysis = res.analysis
        validation = res.validation
        resp = res.response

        # Evaluation checks
        # 1. Fact Extraction
        facts_ok = len(analysis.extracted_facts) > 0 if analysis else False
        # 2. Legal Issue
        issues_ok = len(analysis.legal_issues) > 0 if analysis else False
        # 3. Citation & Rule Matching
        cit_ok = False
        if analysis and analysis.legal_citations:
            target_art = sc.get("expected_article")
            if target_art:
                cit_ok = any(target_art in c.article for c in analysis.legal_citations)
            else:
                cit_ok = True
        elif sc.get("expected_insufficient_handling"):
            cit_ok = True  # correctly handled

        # 4. Exception Handling
        ex_ok = True
        exp_ex = sc.get("expected_exception_keywords")
        if exp_ex and analysis:
            raw_comb = (analysis.raw_llm_response + " " + " ".join(analysis.exceptions)).lower()
            ex_ok = any(kw.lower() in raw_comb for kw in exp_ex)

        # 5. Missing facts
        miss_ok = True
        if sc.get("expected_missing_facts_keywords") and analysis:
            comb = (analysis.raw_llm_response + " " + " ".join(analysis.missing_facts)).lower()
            miss_ok = any(kw.lower() in comb for kw in sc["expected_missing_facts_keywords"])

        # 6. Temporal Awareness
        temp_ok = True
        if sc.get("expected_temporal_keywords") and analysis:
            comb = (analysis.raw_llm_response + " " + " ".join(analysis.temporal_notes)).lower()
            temp_ok = any(kw.lower() in comb for kw in sc["expected_temporal_keywords"])

        # 7. Unsupported claims / Validation
        val_status = validation.validation_status if validation else "N/A"
        no_hallucination = len(validation.hallucinated_citations) == 0 if validation else True

        sc_result = {
            "id": sc_id,
            "category": cat,
            "question": q,
            "latency_sec": round(lat, 2),
            "inference_time_sec": round(analysis.inference_time_sec if analysis else 0.0, 2),
            "fact_extraction_ok": facts_ok,
            "legal_issues_ok": issues_ok,
            "rule_matching_ok": cit_ok,
            "exception_handling_ok": ex_ok,
            "missing_facts_ok": miss_ok,
            "temporal_ok": temp_ok,
            "validation_status": val_status,
            "no_hallucination": no_hallucination,
            "conclusion": analysis.conclusion if analysis else "",
            "extracted_facts": analysis.extracted_facts if analysis else [],
            "legal_issues": analysis.legal_issues if analysis else [],
            "missing_facts": analysis.missing_facts if analysis else [],
            "temporal_notes": analysis.temporal_notes if analysis else [],
            "verified_citations": [f"{c.get('document_number')} {c.get('article')} {c.get('clause')}" for c in (validation.verified_citations if validation else [])]
        }
        results.append(sc_result)

        print(f"-> Thời gian: {lat:.2f}s (LLM: {analysis.inference_time_sec:.2f}s)")
        print(f"-> Fact Extraction: {analysis.extracted_facts if analysis else []}")
        print(f"-> Legal Issues:    {analysis.legal_issues if analysis else []}")
        print(f"-> Missing Facts:   {analysis.missing_facts if analysis else []}")
        print(f"-> Temporal Notes:  {analysis.temporal_notes if analysis else []}")
        print(f"-> Validation:      {val_status} (Zero Hallucination: {no_hallucination})")
        print(f"-> Kết luận:        {analysis.conclusion[:150] if analysis else ''}...")

    ram_end = proc.memory_info().rss / (1024 * 1024)

    # Summary table
    print("\n" + "=" * 100)
    print("BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ 7 TIÊU CHÍ FACT-TO-LAW")
    print("=" * 100)
    print(f"{'ID':<7} | {'Facts':<6} | {'Issues':<6} | {'Rule':<6} | {'Except':<6} | {'Missing':<7} | {'Temp':<6} | {'Val Stat':<8} | {'Lat (s)':<7}")
    print("-" * 100)
    for r in results:
        fmt = lambda b: "ĐẠT" if b else "CHƯA"
        print(f"{r['id']:<7} | {fmt(r['fact_extraction_ok']):<6} | {fmt(r['legal_issues_ok']):<6} | {fmt(r['rule_matching_ok']):<6} | {fmt(r['exception_handling_ok']):<6} | {fmt(r['missing_facts_ok']):<7} | {fmt(r['temporal_ok']):<6} | {r['validation_status']:<8} | {r['latency_sec']:<7.2f}")

    print(f"\nTổng thời gian kiểm thử: {total_time:.2f}s (Trung bình: {total_time/len(results):.2f}s / query)")
    print(f"RAM sử dụng: {ram_end:.2f} MB (Delta: {ram_end - ram_start:+.2f} MB)")

    # Save to JSON report
    report_file = ROOT_DIR / "reports" / "audit_phase4_3_fact_to_law.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu kết quả chi tiết vào: {report_file}")

if __name__ == "__main__":
    run_evaluation()
