# tests/audit_stage2_validation_agent.py
"""
Audit script for ValidationAgent scenarios:
Scenario 1: Number (percentage/days) matches directly within cited clause.
Scenario 2: Number appears in sibling clause in the same article, but NOT in cited clause.
Scenario 3: Correct Article, but wrong Clause cited (or non-existent chunk/article).
Scenario 4: Hallucinated number / condition not found anywhere in source context.
Scenario 5: Citation-Answer Consistency check (mismatch between answer body and cited source).
Scenario 6: Completely missing law / unsupported law in knowledge base.
"""
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.validation_agent import ValidationAgent, ValidationResult
from src.agents.legal_analysis_agent import LegalAnalysisResult, LegalCitation
from src.agents.retrieval_agent import EnrichedChunk, RetrievalContext

def run_validation_scenarios():
    validator = ValidationAgent()
    
    # Real chunks from BHXH 2024 Điều 45 Khoản 1 and Khoản 2
    chunk_k1 = EnrichedChunk(
        chunk_id="41_2024_QH15_art_45_cl_1_218",
        document_name="Luật Bảo hiểm xã hội 2024",
        document_number="41/2024/QH15",
        chapter="Chương III",
        article="Điều 45",
        clause="Khoản 1",
        point=None,
        page_start=35,
        page_end=35,
        text="Điều 45. Mức hưởng chế độ ốm đau\n1. Người lao động hưởng chế độ ốm đau theo quy định tại khoản 1 và điểm a khoản 2 Điều 42 của Luật này thì mức hưởng tính theo tháng bằng 75% mức tiền lương làm căn cứ đóng bảo hiểm xã hội của tháng liền kề trước khi nghỉ việc.",
        score=0.9,
        retrieval_rank=1,
        retrieval_method="hybrid"
    )
    
    chunk_k2 = EnrichedChunk(
        chunk_id="41_2024_QH15_art_45_cl_2_219",
        document_name="Luật Bảo hiểm xã hội 2024",
        document_number="41/2024/QH15",
        chapter="Chương III",
        article="Điều 45",
        clause="Khoản 2",
        point=None,
        page_start=35,
        page_end=35,
        text="Điều 45. Mức hưởng chế độ ốm đau\n2. Người lao động mắc bệnh thuộc Danh mục bệnh cần chữa trị dài ngày do Bộ trưởng Bộ Y tế ban hành thì mức hưởng chế độ ốm đau tính theo tháng như sau:\na) Bằng 75% mức tiền lương làm căn cứ đóng bảo hiểm xã hội của tháng liền kề trước khi nghỉ việc nếu đã đóng bảo hiểm xã hội từ đủ 30 năm trở lên;\nb) Bằng 65% nếu đã đóng bảo hiểm xã hội từ đủ 15 năm đến dưới 30 năm;\nc) Bằng 50% nếu đã đóng bảo hiểm xã hội dưới 15 năm.",
        score=0.85,
        retrieval_rank=2,
        retrieval_method="parent_child_expanded",
        is_parent_child_expanded=True
    )
    
    chunks = [chunk_k1, chunk_k2]
    
    scenarios = [
        {
            "id": "scenario_1_exact_match",
            "name": "Số liệu đúng trong Khoản được trích dẫn (75% ở Khoản 2 Điều 45)",
            "query": "Mức hưởng chế độ ốm đau thông thường của người lao động là bao nhiêu?",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng chế độ ốm đau thông thường của người lao động bằng 75% mức tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 2",
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_2_219",
                        quote_snippet="bằng 75% tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại khoản 1 Điều này"
                    )
                ],
                conditions=["Nghỉ việc theo khoản 1 Điều 43 và Điều 44"],
                rates_and_deadlines=["75%"]
            )
        },
        {
            "id": "scenario_2_number_in_sibling_clause",
            "name": "Số liệu chỉ xuất hiện ở Khoản khác (Khoản 2 có 75%, nhưng trích dẫn Khoản 1)",
            "query": "Mức hưởng chế độ ốm đau thông thường là bao nhiêu?",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng bằng 75% mức tiền lương làm căn cứ đóng bảo hiểm xã hội.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 1", # Intentional mistake: 75% is in Khoản 2, not Khoản 1!
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_1_218"
                    )
                ],
                conditions=["Tính theo tháng"],
                rates_and_deadlines=["75%"]
            )
        },
        {
            "id": "scenario_3_wrong_clause",
            "name": "Trích dẫn đúng Điều nhưng sai Khoản (Khoản 99 không tồn tại)",
            "query": "Điều kiện hưởng ốm đau",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Người lao động được hưởng chế độ ốm đau theo quy định.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Bảo hiểm xã hội 2024",
                        document_number="41/2024/QH15",
                        article="Điều 45. Trợ cấp ốm đau",
                        clause="Khoản 99", # Non-existent clause
                        page_start=35,
                        chunk_id="41_2024_QH15_art_45_cl_99_999"
                    )
                ],
                conditions=[],
                rates_and_deadlines=[]
            )
        },
        {
            "id": "scenario_4_hallucinated_facts",
            "name": "Câu trả lời có thông tin/con số không được hỗ trợ bởi văn bản (100% lương)",
            "query": "Mức hưởng ốm đau đặc biệt",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Mức hưởng ốm đau được chi trả 100% tiền lương theo quy định đặc biệt.",
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
                conditions=[],
                rates_and_deadlines=["100%"] # 100% does not exist in Khoản 2 (it's in Khoản 4)
            )
        },
        {
            "id": "scenario_5_citation_inconsistency",
            "name": "Kết luận không phù hợp với căn cứ pháp lý (Trích Điều 45 ốm đau nhưng kết luận thai sản)",
            "query": "Thời gian nghỉ sinh con của lao động nữ",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Lao động nữ sinh con được nghỉ thai sản trước và sau khi sinh là 6 tháng.",
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
                conditions=[],
                rates_and_deadlines=["6 tháng"]
            )
        },
        {
            "id": "scenario_6_missing_law",
            "name": "Trường hợp thiếu văn bản pháp luật trong Knowledge Base (Luật Hàng không)",
            "query": "Bồi thường chậm chuyến bay theo Luật Hàng không dân dụng Việt Nam",
            "analysis": LegalAnalysisResult(
                status="success",
                is_sufficient=True,
                conclusion="Hãng hàng không phải bồi thường tiền chậm chuyến bay cho hành khách.",
                legal_citations=[
                    LegalCitation(
                        document_name="Luật Hàng không dân dụng Việt Nam",
                        document_number="66/2006/QH11", # Law not in KB
                        article="Điều 160",
                        clause="Khoản 1",
                        page_start=1
                    )
                ],
                conditions=[],
                rates_and_deadlines=[]
            )
        }
    ]
    
    results = []
    print("="*75)
    print("AUDIT STAGE 2: VALIDATION AGENT SCENARIOS AUDIT")
    print("="*75)
    
    for sc in scenarios:
        ret_context = RetrievalContext(
            query=sc["query"],
            expanded_query=sc["query"],
            primary_chunks=[chunk_k1],
            expanded_chunks=[chunk_k2],
            all_chunks=chunks,
            unique_articles=["Điều 45"],
            total_retrieved=2
        )
        
        val_res = validator.validate(
            analysis_result=sc["analysis"],
            retrieval_context=ret_context
        )
        
        print(f"\n[{sc['id'].upper()}] - {sc['name']}")
        print(f"  Status: {val_res.validation_status} (is_valid={val_res.is_valid})")
        print(f"  Passed Checks ({len(val_res.passed_checks)}):")
        for pc in val_res.passed_checks:
            print(f"    + {pc}")
        if val_res.warning_messages:
            print(f"  Warnings ({len(val_res.warning_messages)}):")
            for w in val_res.warning_messages:
                print(f"    ! {w}")
        if val_res.error_messages:
            print(f"  Errors ({len(val_res.error_messages)}):")
            for err in val_res.error_messages:
                print(f"    X {err}")
                
        results.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "validation_status": val_res.validation_status,
            "is_valid": val_res.is_valid,
            "passed_checks": val_res.passed_checks,
            "warning_messages": val_res.warning_messages,
            "error_messages": val_res.error_messages,
            "hallucinated_citations": val_res.hallucinated_citations,
            "unsupported_facts": val_res.unsupported_facts
        })
        
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    with open("data/processed/audit_validation_scenarios.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open("reports/audit_validation_scenarios.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n" + "="*75)
    print("VALIDATION SCENARIOS TEST COMPLETED! Saved to data/processed & reports")
    print("="*75)

if __name__ == "__main__":
    run_validation_scenarios()
