import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Set

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.intent_agent import IntentAgent
from src.agents.retrieval_agent import RetrievalAgent

def run_rigorous_evaluation():
    benchmark_path = ROOT_DIR / "tests" / "gold_standard_benchmark.json"
    with open(benchmark_path, "r", encoding="utf-8") as f:
        gold_standards = json.load(f)

    intent_agent = IntentAgent()
    retrieval_agent = RetrievalAgent()

    # Filter only in-scope questions for retrieval evaluation
    in_scope_benchmarks = [item for item in gold_standards if item.get("domain") != "out_of_scope"]
    total_queries = len(in_scope_benchmarks)

    # Metrics counters
    article_hits_before = 0
    article_hits_after = 0
    clause_hits_before = 0
    clause_hits_after = 0
    clause_all_hits_after = 0

    results_detail = []

    print("="*95)
    print("KIỂM TOÁN VÀ ĐÁNH GIÁ CHẤT LƯỢNG RETRIEVAL TRƯỚC VÀ SAU PARENT-CHILD EXPANSION")
    print("="*95)
    print(f"Tổng số câu hỏi đánh giá hợp lệ (In-Scope): {total_queries}\n")

    t_start = time.time()

    for item in in_scope_benchmarks:
        qid = item["id"]
        q = item["query"]
        target_doc = item["target_document"]
        target_art = item["target_article"]
        target_clauses = item["target_clauses"]

        # 1. Intent & Expand
        intent_res = intent_agent.classify_intent(q)

        # 2. Retrieval
        t0 = time.time()
        ret_res = retrieval_agent.retrieve(intent_res.normalized_query, intent_res.expanded_query)
        latency = time.time() - t0

        # --- A. Evaluation BEFORE Expansion (Primary Chunks Only) ---
        primary_chunks = ret_res.primary_chunks
        has_art_before = False
        found_clauses_before = set()

        for c in primary_chunks:
            if target_doc in c.document_number and (target_art in c.article or target_art.replace(".", "") in c.article):
                has_art_before = True
                for tc in target_clauses:
                    if tc in c.clause:
                        found_clauses_before.add(tc)

        # --- B. Evaluation AFTER Expansion (All Chunks) ---
        all_chunks = ret_res.all_chunks
        has_art_after = False
        found_clauses_after = set()
        matched_chunks_info = []

        for c in all_chunks:
            if target_doc in c.document_number and (target_art in c.article or target_art.replace(".", "") in c.article):
                has_art_after = True
                for tc in target_clauses:
                    if tc in c.clause:
                        found_clauses_after.add(tc)
                        matched_chunks_info.append(f"{c.clause} ({c.retrieval_method})")

        has_clause_before = len(found_clauses_before) > 0
        has_clause_after = len(found_clauses_after) > 0
        all_clauses_after = len(found_clauses_after) == len(target_clauses)

        if has_art_before:
            article_hits_before += 1
        if has_art_after:
            article_hits_after += 1
        if has_clause_before:
            clause_hits_before += 1
        if has_clause_after:
            clause_hits_after += 1
        if all_clauses_after:
            clause_all_hits_after += 1

        # Status tag
        if has_clause_after:
            if has_clause_before:
                status_tag = "DIRECT HIT (Before & After)"
            else:
                status_tag = "EXPANDED HIT (Via Parent-Child)"
        elif has_art_after:
            status_tag = "ARTICLE ONLY (Missing Clause)"
        else:
            status_tag = "MISSED (Not in Top Chunks)"

        print(f"[{qid}] {status_tag:32} | {q[:50]}...")
        print(f"      Mục tiêu: {target_art} {target_clauses}")
        print(f"      Trước Exp: Clauses {list(found_clauses_before)} | Sau Exp: Clauses {list(found_clauses_after)} ({latency:.2f}s)")

        results_detail.append({
            "id": qid,
            "query": q,
            "target_article": target_art,
            "target_clauses": target_clauses,
            "article_before": has_art_before,
            "article_after": has_art_after,
            "clause_before": has_clause_before,
            "clause_after": has_clause_after,
            "all_clauses_after": all_clauses_after,
            "found_before": list(found_clauses_before),
            "found_after": list(found_clauses_after),
            "latency_sec": latency
        })

    total_time = time.time() - t_start

    pct_art_before = (article_hits_before / total_queries) * 100
    pct_art_after = (article_hits_after / total_queries) * 100
    pct_cl_before = (clause_hits_before / total_queries) * 100
    pct_cl_after = (clause_hits_after / total_queries) * 100
    pct_cl_all_after = (clause_all_hits_after / total_queries) * 100

    print("\n" + "="*95)
    print("BÁO CÁO THỐNG KÊ RETRIEVAL TRƯỚC VÀ SAU PARENT-CHILD EXPANSION:")
    print("="*95)
    print(f"1. Tổng số câu hỏi kiểm thử:                     {total_queries}")
    print(f"2. Article Hit Rate (Trước Expansion - Primary): {article_hits_before}/{total_queries} ({pct_art_before:.1f}%)")
    print(f"3. Article Hit Rate (Sau Expansion - Total):     {article_hits_after}/{total_queries} ({pct_art_after:.1f}%)")
    print(f"4. Clause Hit Rate (Trước Expansion - Primary):  {clause_hits_before}/{total_queries} ({pct_cl_before:.1f}%)")
    print(f"5. Clause Hit Rate (Sau Expansion - Total):      {clause_hits_after}/{total_queries} ({pct_cl_after:.1f}%)")
    print(f"6. Full Clause Hit Rate (Tìm thấy TẤT CẢ Khoản): {clause_all_hits_after}/{total_queries} ({pct_cl_all_after:.1f}%)")
    print(f"7. Chênh lệch cải thiện nhờ Parent-Child:        +{clause_hits_after - clause_hits_before} câu hỏi (+{pct_cl_after - pct_cl_before:.1f}%)")
    print("="*95)

    # Save to json report
    out_path = ROOT_DIR / "data" / "processed" / "retrieval_expansion_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_queries": total_queries,
            "article_hit_before": article_hits_before,
            "article_hit_after": article_hits_after,
            "clause_hit_before": clause_hits_before,
            "clause_hit_after": clause_hits_after,
            "all_clauses_hit_after": clause_all_hits_after,
            "pct_article_before": pct_art_before,
            "pct_article_after": pct_art_after,
            "pct_clause_before": pct_cl_before,
            "pct_clause_after": pct_cl_after,
            "pct_all_clauses_after": pct_cl_all_after,
            "details": results_detail
        }, f, ensure_ascii=False, indent=2)

    print(f"\nĐã lưu chi tiết vào: {out_path}")

if __name__ == "__main__":
    run_rigorous_evaluation()
