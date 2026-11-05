# tests/audit_stage3_multi_agent_suite.py
"""
Comprehensive Multi-Agent Test Suite:
Runs the complete multi-agent pipeline on 7 representative categories:
1. Labor law (TC1_LABOR)
2. Social insurance (TC2_BHXH)
3. Multi-intent / multi-clause (TC3_MULTI)
4. Underspecified / vague query (TC4_VAGUE)
5. Out of scope (TC5_OOS)
6. Missing in KB / Law not covered (TC6_MISSING)
7. Adversarial / confusing keywords (TC7_CONFUSING)

Measures:
- Agent latency breakdowns (Intent, Retrieval, Legal Analysis, Validation, Response)
- Process RAM (RSS in MB) vs System RAM (Windows total in GB and %)
- Step-by-step verification, warnings, citations, and answers
"""
import sys
import os
import time
import json
import psutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.orchestrator import LegalAgentOrchestrator

def run_suite():
    print("="*80)
    print("STARTING COMPREHENSIVE MULTI-AGENT TEST SUITE")
    print("="*80)
    
    orchestrator = LegalAgentOrchestrator()
    
    test_cases = [
        {
            "category": "1. Labor Law",
            "id": "TC1_LABOR",
            "query": "Thời gian thử việc tối đa đối với người làm công việc có chức danh nghề nghiệp cần trình độ đại học trở lên là bao nhiêu ngày?",
            "expected_domain": "labor_law"
        },
        {
            "category": "2. Social Insurance",
            "id": "TC2_BHXH",
            "query": "Mức hưởng chế độ ốm đau thông thường của người lao động bằng bao nhiêu phần trăm tiền lương?",
            "expected_domain": "social_insurance"
        },
        {
            "category": "3. Multi-intent / Multi-point",
            "id": "TC3_MULTI",
            "query": "Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng lao động trong những trường hợp nào và phải báo trước bao nhiêu ngày?",
            "expected_domain": "labor_law"
        },
        {
            "category": "4. Vague / Underspecified",
            "id": "TC4_VAGUE",
            "query": "Nghỉ việc được hưởng tiền gì?",
            "expected_domain": "labor_law"
        },
        {
            "category": "5. Out of Scope",
            "id": "TC5_OOS",
            "query": "Thời hạn chuyển nhượng quyền sử dụng đất nông nghiệp theo Luật Đất đai là bao nhiêu năm?",
            "expected_domain": "out_of_scope"
        },
        {
            "category": "6. Missing in KB",
            "id": "TC6_MISSING",
            "query": "Theo Luật Hàng không dân dụng Việt Nam, hành khách bị hủy chuyến bay được bồi thường tối đa bao nhiêu tiền?",
            "expected_domain": "out_of_scope"
        },
        {
            "category": "7. Adversarial / Confusing Keywords",
            "id": "TC7_CONFUSING",
            "query": "Tôi muốn biết hợp đồng thử việc bảo hiểm xã hội tính bao nhiêu phần trăm lương làm thêm giờ?",
            "expected_domain": "mixed"
        }
    ]
    
    results = []
    
    for tc in test_cases:
        print("\n" + "-"*75)
        print(f"RUNNING [{tc['id']}] ({tc['category']}): {tc['query']}")
        print("-"*75)
        
        t0 = time.time()
        res = orchestrator.process_query(tc["query"])
        elapsed = time.time() - t0
        
        domain = res.intent.domain
        status_val = res.validation.validation_status if res.validation else "SKIPPED/OOS"
        warnings = res.validation.warning_messages if res.validation else []
        errors = res.validation.error_messages if res.validation else []
        
        print(f"Domain Classified:    {domain}")
        print(f"Validation Status:    {status_val} (Warnings: {len(warnings)}, Errors: {len(errors)})")
        print(f"Total Time:           {res.timing.total_time*1000:.2f} ms ({res.timing.total_time:.2f} s)")
        print(f"Process RAM RSS:      Before={res.resources.process_ram_before_mb:.1f} MB | After={res.resources.process_ram_after_mb:.1f} MB (Delta: {res.resources.process_ram_delta_mb:.1f} MB)")
        print(f"System RAM (Windows): {res.resources.system_ram_used_gb:.2f} GB / {res.resources.system_ram_total_gb:.2f} GB ({res.resources.system_ram_percent}%)")
        print(f"Agent Latency Breakdown:")
        print(f"   - IntentAgent:        {res.timing.intent_time*1000:.2f} ms")
        print(f"   - RetrievalAgent:     {res.timing.retrieval_time*1000:.2f} ms")
        print(f"   - LegalAnalysisAgent: {res.timing.analysis_time*1000:.2f} ms")
        print(f"   - ValidationAgent:    {res.timing.validation_time*1000:.2f} ms")
        print(f"   - ResponseAgent:      {res.timing.response_time*1000:.2f} ms")
        
        if res.retrieval:
            print(f"Retrieval Context:    {res.retrieval.total_retrieved} chunks across articles {res.retrieval.unique_articles}")
            
        print("\nDirect Answer Snippet:")
        print(f"   {res.response.conclusion[:200]}...")
        
        if res.response.legal_basis:
            print("\nLegal Basis:")
            for b in res.response.legal_basis:
                print(f"   * {b.get('document')} - {b.get('article')}, {b.get('clause')}")
                
        results.append({
            "test_id": tc["id"],
            "category": tc["category"],
            "query": tc["query"],
            "expected_domain": tc["expected_domain"],
            "actual_domain": domain,
            "validation_status": status_val,
            "warnings": warnings,
            "errors": errors,
            "timing_ms": res.timing.to_dict(),
            "resources": res.resources.to_dict(),
            "answer_summary": res.response.conclusion,
            "legal_basis": res.response.legal_basis
        })
        
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    with open("data/processed/audit_multi_agent_suite.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open("reports/audit_multi_agent_suite.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*80)
    print("MULTI-AGENT TEST SUITE COMPLETED SUCCESSFULLY!")
    print("Results saved to: data/processed & reports")
    print("="*80)

if __name__ == "__main__":
    run_suite()
