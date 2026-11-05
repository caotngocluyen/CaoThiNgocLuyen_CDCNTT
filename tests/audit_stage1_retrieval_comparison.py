import sys
import os
import re
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
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever
from src.retrieval.embedding import LegalEmbeddingModel
from config import (
    BM25_INDEX_PATH,
    CHUNKS_JSON_PATH,
    RETRIEVAL_TOP_K,
    RETRIEVAL_CANDIDATE_POOL,
    PARENT_CHILD_EXPAND,
    MAX_PARENT_CHILD_SIBLINGS
)

def is_art_match(target_doc: str, target_art: str, doc_num: str, chunk_art: str) -> bool:
    if target_doc not in doc_num:
        return False
    clean_target = target_art.strip().rstrip(".")
    pattern = rf"^{re.escape(clean_target)}(\.|\s|$)"
    return bool(re.search(pattern, chunk_art.strip()))

def run_3stage_retrieval_audit():
    print("="*100)
    print("KIỂM TOÁN 3 GIAI ĐOẠN TRUY XUẤT: RAW QUERY -> EXPANDED QUERY -> PARENT-CHILD EXPANSION")
    print("="*100)

    # 1. Load Index and Retriever
    bm25 = BM25Searcher(BM25_INDEX_PATH)
    bm25.load_index()
    emb = LegalEmbeddingModel()
    dense = DenseVectorSearcher(emb)
    retriever = HybridLegalRetriever(bm25, dense)
    intent_agent = IntentAgent()

    # Build sibling chunks index for parent-child expansion
    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    article_index = {}
    for c in all_chunks:
        k = f"{c['document_number']}|||{c['article']}"
        if k not in article_index:
            article_index[k] = []
        article_index[k].append(c)

    # Load Gold Standard
    with open(ROOT_DIR / "tests" / "gold_standard_benchmark.json", "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    # Metrics
    stage_a_art_hits = 0
    stage_a_cl_hits = 0
    stage_b_art_hits = 0
    stage_b_cl_hits = 0
    stage_c_art_hits = 0
    stage_c_cl_hits = 0
    stage_c_all_cl_hits = 0

    results = []

    print(f"Tổng số câu hỏi kiểm thử: {len(benchmarks)}\n")

    for item in benchmarks:
        qid = item["id"]
        raw_q = item["query"]
        target_doc = item["target_document"]
        target_art = item["target_article"]
        target_clauses = item["target_clauses"]

        # Intent Expansion
        intent_res = intent_agent.classify_intent(raw_q)
        expanded_q = intent_res.expanded_query

        # STAGE A: Raw query retrieval (Hybrid RRF Top-K)
        t0 = time.time()
        stage_a_hits = retriever.search(raw_q, top_k=RETRIEVAL_TOP_K, candidate_pool=RETRIEVAL_CANDIDATE_POOL)
        time_a = time.time() - t0

        has_art_a = False
        found_cl_a = set()
        for r in stage_a_hits:
            if is_art_match(target_doc, target_art, r.document_number, r.article):
                has_art_a = True
                for tc in target_clauses:
                    if tc in r.clause:
                        found_cl_a.add(tc)

        # STAGE B: Expanded query retrieval (Hybrid RRF Top-K)
        t0 = time.time()
        stage_b_hits = retriever.search(expanded_q, top_k=RETRIEVAL_TOP_K, candidate_pool=RETRIEVAL_CANDIDATE_POOL)
        time_b = time.time() - t0

        has_art_b = False
        found_cl_b = set()
        for r in stage_b_hits:
            if is_art_match(target_doc, target_art, r.document_number, r.article):
                has_art_b = True
                for tc in target_clauses:
                    if tc in r.clause:
                        found_cl_b.add(tc)

        # STAGE C: Post Parent-Child Expansion on Stage B
        t0 = time.time()
        stage_c_all = list(stage_b_hits)
        seen_cids = {r.chunk_id for r in stage_b_hits}
        processed_articles = set()

        for r in stage_b_hits:
            art_key = f"{r.document_number}|||{r.article}"
            if art_key in processed_articles:
                continue
            processed_articles.add(art_key)
            siblings = article_index.get(art_key, [])
            added = 0
            for sib in siblings:
                if sib["chunk_id"] not in seen_cids and added < MAX_PARENT_CHILD_SIBLINGS:
                    seen_cids.add(sib["chunk_id"])
                    stage_c_all.append(sib)
                    added += 1

        has_art_c = False
        found_cl_c = set()
        for c in stage_c_all:
            c_doc = getattr(c, "document_number", c.get("document_number") if isinstance(c, dict) else "")
            c_art = getattr(c, "article", c.get("article") if isinstance(c, dict) else "")
            c_cl = getattr(c, "clause", c.get("clause") if isinstance(c, dict) else "")

            if is_art_match(target_doc, target_art, c_doc, c_art):
                has_art_c = True
                for tc in target_clauses:
                    if tc in c_cl:
                        found_cl_c.add(tc)

        # Update counters
        if has_art_a: stage_a_art_hits += 1
        if len(found_cl_a) > 0: stage_a_cl_hits += 1

        if has_art_b: stage_b_art_hits += 1
        if len(found_cl_b) > 0: stage_b_cl_hits += 1

        if has_art_c: stage_c_art_hits += 1
        if len(found_cl_c) > 0: stage_c_cl_hits += 1
        if len(found_cl_c) == len(target_clauses): stage_c_all_cl_hits += 1

        results.append({
            "id": qid,
            "raw_query": raw_q,
            "expanded_query": expanded_q,
            "target_article": target_art,
            "target_clauses": target_clauses,
            "stage_a": {"art_hit": has_art_a, "clauses": list(found_cl_a)},
            "stage_b": {"art_hit": has_art_b, "clauses": list(found_cl_b)},
            "stage_c": {"art_hit": has_art_c, "clauses": list(found_cl_c), "all_clauses": len(found_cl_c) == len(target_clauses)}
        })

        print(f"[{qid}] Mục tiêu: {target_art} {target_clauses}")
        print(f"   * Stage A (Raw):      Art={has_art_a:5} | Clauses={list(found_cl_a)}")
        print(f"   * Stage B (Expanded): Art={has_art_b:5} | Clauses={list(found_cl_b)}")
        print(f"   * Stage C (P-C Exp):  Art={has_art_c:5} | Clauses={list(found_cl_c)}")

    n = len(benchmarks)
    print("\n" + "="*100)
    print("KẾT QUẢ ĐỐI SOÁNH ĐỘC LẬP 3 GIAI ĐOẠN:")
    print("="*100)
    print(f"1. GIAI ĐOẠN A (CÂU HỎI GỐC - RAW QUERY):")
    print(f"   - Article Hit Rate: {stage_a_art_hits}/{n} ({stage_a_art_hits/n*100:.1f}%)")
    print(f"   - Clause Hit Rate:  {stage_a_cl_hits}/{n} ({stage_a_cl_hits/n*100:.1f}%)")

    print(f"\n2. GIAI ĐOẠN B (SAU INTENT QUERY EXPANSION):")
    print(f"   - Article Hit Rate: {stage_b_art_hits}/{n} ({stage_b_art_hits/n*100:.1f}%) [Δ: {stage_b_art_hits - stage_a_art_hits:+d}]")
    print(f"   - Clause Hit Rate:  {stage_b_cl_hits}/{n} ({stage_b_cl_hits/n*100:.1f}%) [Δ: {stage_b_cl_hits - stage_a_cl_hits:+d}]")

    print(f"\n3. GIAI ĐOẠN C (SAU PARENT-CHILD CONTEXT EXPANSION):")
    print(f"   - Article Hit Rate: {stage_c_art_hits}/{n} ({stage_c_art_hits/n*100:.1f}%)")
    print(f"   - Clause Hit Rate:  {stage_c_cl_hits}/{n} ({stage_c_cl_hits/n*100:.1f}%) [Δ so với Stage B: {stage_c_cl_hits - stage_b_cl_hits:+d}]")
    print(f"   - Full Clause Hit:  {stage_c_all_cl_hits}/{n} ({stage_c_all_cl_hits/n*100:.1f}%)")

    print("="*100)

    # Save to json file
    out_file = ROOT_DIR / "data" / "processed" / "audit_3stage_retrieval.json"
    reports_out_file = ROOT_DIR / "reports" / "audit_3stage_retrieval.json"
    os.makedirs(ROOT_DIR / "reports", exist_ok=True)
    payload = {
        "total": n,
        "stage_a": {"art_hits": stage_a_art_hits, "cl_hits": stage_a_cl_hits, "art_pct": stage_a_art_hits/n*100, "cl_pct": stage_a_cl_hits/n*100},
        "stage_b": {"art_hits": stage_b_art_hits, "cl_hits": stage_b_cl_hits, "art_pct": stage_b_art_hits/n*100, "cl_pct": stage_b_cl_hits/n*100},
        "stage_c": {"art_hits": stage_c_art_hits, "cl_hits": stage_c_cl_hits, "all_cl_hits": stage_c_all_cl_hits, "art_pct": stage_c_art_hits/n*100, "cl_pct": stage_c_cl_hits/n*100, "all_cl_pct": stage_c_all_cl_hits/n*100},
        "details": results
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(reports_out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nĐã lưu chi tiết vào: {out_file} và {reports_out_file}")

if __name__ == "__main__":
    run_3stage_retrieval_audit()
