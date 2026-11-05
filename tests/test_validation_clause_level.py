# tests/test_validation_clause_level.py
"""
Strict Clause-Level & Condition Grounding Test Suite for ValidationAgent:
Evaluates all requirements from Phase 3 Final Audit:
1. 75% tại Khoản 2 Điều 45: PASSED
2. 75% tại Khoản 1 Điều 45: Không được PASSED (WARNING)
3. 65% tại Khoản 3 Điều 45 (đúng điều kiện: từ đủ 30 năm trở lên): PASSED
4. 55% tại Khoản 3 Điều 45 (đúng điều kiện: từ đủ 15 năm đến dưới 30 năm): PASSED
5. 50% tại Khoản 3 Điều 45 (đúng điều kiện: dưới 15 năm): PASSED
6. 65% tại Khoản 2 Điều 45: Không được PASSED (WARNING)
7. 65% tại Khoản 3 Điều 45 nhưng SAI điều kiện (gán với 'dưới 15 năm'): FAILED
"""
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.validation_agent import ValidationAgent
from src.agents.legal_analysis_agent import LegalAnalysisResult, LegalCitation
from src.agents.retrieval_agent import EnrichedChunk, RetrievalContext

def run_tests():
    validator = ValidationAgent()
    
    # Official chunks for Điều 45 Luật BHXH 2024 (41/2024/QH15)
    chunk_k1 = EnrichedChunk(
        chunk_id="41_2024_QH15_art_45_cl_1_218",
        document_name="Luật Bảo hiểm xã hội 2024",
        document_number="41/2024/QH15",
        chapter="Chương III",
        article="Điều 45. Trợ cấp ốm đau",
        clause="Khoản 1",
        point=None,
        page_start=35,
        page_end=35,
        text="[Luật Bảo hiểm xã hội - Điều 45. Trợ cấp ốm đau - Khoản 1]\n1. Mức hưởng trợ cấp ốm đau được tính theo tháng và tính trên căn cứ sau đây:\na) Tiền lương làm căn cứ đóng bảo hiểm xã hội của tháng gần nhất trước tháng nghỉ việc hưởng chế độ ốm đau;\nb) Tiền lương làm căn cứ đóng bảo hiểm xã hội của tháng đầu tiên tham gia bảo hiểm xã hội hoặc tháng tham gia trở lại nếu phải nghỉ việc hưởng chế độ ốm đau ngay trong tháng đầu tiên tham gia hoặc tháng tham gia trở lại.",
        score=0.9,
        retrieval_rank=1,
        retrieval_method="hybrid"
    )

    chunk_k2 = EnrichedChunk(
        chunk_id="41_2024_QH15_art_45_cl_2_219",
        document_name="Luật Bảo hiểm xã hội 2024",
        document_number="41/2024/QH15",
        chapter="Chương III",
        article="Điều 45. Trợ cấp ốm đau",
        clause="Khoản 2",
        point=None,
        page_start=35,
        page_end=35,
        text="[Luật Bảo hiểm xã hội - Điều 45. Trợ cấp ốm đau - Khoản 2]\n2. Mức hưởng trợ cấp ốm đau của người lao động quy định tại khoản 1 Điều 43 và Điều 44 của Luật này bằng 75% tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này.",
        score=0.88,
        retrieval_rank=2,
        retrieval_method="hybrid"
    )

    chunk_k3 = EnrichedChunk(
        chunk_id="41_2024_QH15_art_45_cl_3_220",
        document_name="Luật Bảo hiểm xã hội 2024",
        document_number="41/2024/QH15",
        chapter="Chương III",
        article="Điều 45. Trợ cấp ốm đau",
        clause="Khoản 3",
        point=None,
        page_start=35,
        page_end=35,
        text="[Luật Bảo hiểm xã hội - Điều 45. Trợ cấp ốm đau - Khoản 3]\n3. Mức hưởng trợ cấp ốm đau của người lao động quy định tại khoản 2 Điều 43 của Luật này được tính như sau:\na) Bằng 65% tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này nếu đã đóng bảo hiểm xã hội bắt buộc từ đủ 30 năm trở lên;\nb) Bằng 55% tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này nếu đã đóng bảo hiểm xã hội bắt buộc từ đủ 15 năm đến dưới 30 năm;\nc) Bằng 50% tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này nếu đã đóng bảo hiểm xã hội bắt buộc dưới 15 năm.",
        score=0.85,
        retrieval_rank=3,
        retrieval_method="parent_child_expanded",
        is_parent_child_expanded=True
    )

    all_d45_chunks = [chunk_k1, chunk_k2, chunk_k3]
    ret_ctx = RetrievalContext(
        query="Mức hưởng chế độ ốm đau",
        expanded_query="Mức hưởng trợ cấp ốm đau",
        primary_chunks=[chunk_k1, chunk_k2],
        expanded_chunks=[chunk_k3],
        all_chunks=all_d45_chunks,
        unique_articles=["Điều 45. Trợ cấp ốm đau"],
        total_retrieved=3
    )

    tests = [
        {
            "id": "T1_75pct_at_Khoan2",
            "name": "75% tại Khoản 2 Điều 45 (Ốm đau thông thường)",
            "expected_status": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng trợ cấp ốm đau của người lao động bằng 75% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 2",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_2_219"
                    )
                ],
                conditions=["Nghỉ việc theo khoản 1 Điều 43 và Điều 44"],
                rates_and_deadlines=["75%"]
            )
        },
        {
            "id": "T2_75pct_at_Khoan1",
            "name": "75% tại Khoản 1 Điều 45 (Sai Khoản - Khoản 1 chỉ quy định căn cứ tiền lương)",
            "expected_status_not": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng trợ cấp ốm đau bằng 75% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 1", # Intentional error: 75% is in Khoản 2, NOT Khoản 1
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_1_218"
                    )
                ],
                conditions=["Theo tháng"],
                rates_and_deadlines=["75%"]
            )
        },
        {
            "id": "T3_65pct_at_Khoan3_correct_cond",
            "name": "65% tại Khoản 3 Điều 45 (Đúng điều kiện: từ đủ 30 năm trở lên)",
            "expected_status": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Người lao động mắc bệnh dài ngày đã đóng bảo hiểm xã hội bắt buộc từ đủ 30 năm trở lên thì mức hưởng bằng 65% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 3",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_3_220"
                    )
                ],
                conditions=["Đã đóng bảo hiểm xã hội bắt buộc từ đủ 30 năm trở lên"],
                rates_and_deadlines=["65%"]
            )
        },
        {
            "id": "T4_55pct_at_Khoan3_correct_cond",
            "name": "55% tại Khoản 3 Điều 45 (Đúng điều kiện: từ đủ 15 năm đến dưới 30 năm)",
            "expected_status": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Người lao động mắc bệnh dài ngày đã đóng bảo hiểm xã hội bắt buộc từ đủ 15 năm đến dưới 30 năm được hưởng bằng 55% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 3",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_3_220"
                    )
                ],
                conditions=["Đã đóng bảo hiểm xã hội bắt buộc từ đủ 15 năm đến dưới 30 năm"],
                rates_and_deadlines=["55%"]
            )
        },
        {
            "id": "T5_50pct_at_Khoan3_correct_cond",
            "name": "50% tại Khoản 3 Điều 45 (Đúng điều kiện: dưới 15 năm)",
            "expected_status": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Người lao động mắc bệnh dài ngày đóng bảo hiểm xã hội bắt buộc dưới 15 năm được hưởng bằng 50% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 3",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_3_220"
                    )
                ],
                conditions=["Đã đóng bảo hiểm xã hội bắt buộc dưới 15 năm"],
                rates_and_deadlines=["50%"]
            )
        },
        {
            "id": "T6_65pct_at_Khoan2",
            "name": "65% tại Khoản 2 Điều 45 (Sai Khoản - Khoản 2 chỉ quy định 7%, còn 65% ở Khoản 3)",
            "expected_status_not": "PASSED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng trợ cấp ốm đau là 65% tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 2", # Intentional error: 65% is in Khoản 3, NOT Khoản 2
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_2_219"
                    )
                ],
                conditions=["Từ đủ 30 năm"],
                rates_and_deadlines=["65%"]
            )
        },
        {
            "id": "T7_65pct_at_Khoan3_wrong_cond",
            "name": "65% tại Khoản 3 Điều 45 nhưng SAI điều kiện (gán với 'dưới 15 năm')",
            "expected_status": "FAILED",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Người lao động đóng bảo hiểm xã hội dưới 15 năm được hưởng mức 65% tiền lương.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 3",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_3_220"
                    )
                ],
                conditions=["Đóng bảo hiểm xã hội dưới 15 năm"],
                rates_and_deadlines=["65%"]
            )
        }
    ]

    print("="*85)
    print("CLAUSE-LEVEL FACT & CONDITION GROUNDING TEST SUITE (DIEU 45 LUAT BHXH 2024)")
    print("="*85)

    all_passed = True
    test_results = []

    for t in tests:
        res = validator.validate(t["analysis"], ret_ctx)
        status = res.validation_status
        is_ok = False

        if "expected_status" in t:
            is_ok = (status == t["expected_status"])
        elif "expected_status_not" in t:
            is_ok = (status != t["expected_status_not"])

        if not is_ok:
            all_passed = False

        status_flag = "[PASS]" if is_ok else "[FAIL TEST]"
        print(f"\n{status_flag} {t['id']}: {t['name']}")
        print(f"       Actual Status: {status} | is_valid={res.is_valid}")
        if res.warning_messages:
            for w in res.warning_messages:
                print(f"       ! Warning: {w}")
        if res.error_messages:
            for e in res.error_messages:
                print(f"       X Error: {e}")

        test_results.append({
            "test_id": t["id"],
            "name": t["name"],
            "actual_status": status,
            "is_valid": res.is_valid,
            "test_passed": is_ok,
            "warnings": res.warning_messages,
            "errors": res.error_messages,
            "passed_checks": res.passed_checks
        })

    print("\n" + "="*85)
    if all_passed:
        print("[SUCCESS] ALL 7 CLAUSE-LEVEL AND CONDITION GROUNDING TESTS PASSED!")
    else:
        print("[FAIL] Some tests did not meet expectations.")
    print("="*85)

    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    with open("data/processed/audit_validation_clause_level.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    with open("reports/audit_validation_clause_level.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_tests()
