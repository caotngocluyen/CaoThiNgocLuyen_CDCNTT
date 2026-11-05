import sys
import json
import time
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from config import (
    BM25_INDEX_PATH,
    VECTOR_DB_DIR,
    CHUNKS_JSON_PATH,
    RRF_K,
    RRF_WEIGHT_BM25,
    RRF_WEIGHT_DENSE,
    MAX_PARENT_CHILD_SIBLINGS
)
from src.retrieval.hybrid_search import BM25Searcher, SearchResult
from src.retrieval.bm25_ngram import BM25NgramSearcher, BM25_NGRAM_INDEX_PATH
from src.utils.logger import get_logger

logger = get_logger("AblationMultilingual")

# Dense searcher wrapper for ChromaDB
class DirectDenseSearcher:
    def __init__(self, model_name: str, collection_name: str):
        self.model_name = model_name
        self.collection_name = collection_name
        logger.info(f"Nạp mô hình dense {model_name} (local_files_only=True)...")
        self.model = SentenceTransformer(model_name, device="cpu", local_files_only=True)
        chroma_path = str(VECTOR_DB_DIR / "chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection(name=collection_name)
        logger.info(f"Đã kết nối collection '{collection_name}' (count: {self.collection.count()})")

    def search(self, query: str, top_k: int = 20) -> List[SearchResult]:
        q_vec = self.model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()
        res = self.collection.query(
            query_embeddings=[q_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        if not res["ids"] or not res["ids"][0]:
            return []

        results = []
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        distances = res["distances"][0]

        for rank, (cid, doc_text, meta, dist) in enumerate(zip(ids, docs, metas, distances), 1):
            sim_score = max(0.0, 1.0 - dist)
            results.append(SearchResult(
                chunk_id=cid,
                document_name=meta.get("document_name", ""),
                document_number=meta.get("document_number", ""),
                chapter=meta.get("chapter", ""),
                article=meta.get("article", ""),
                clause=meta.get("clause", ""),
                point=meta.get("point") if meta.get("point") else None,
                page_start=meta.get("page_start", 1),
                page_end=meta.get("page_end", 1),
                text=doc_text,
                score=sim_score,
                dense_rank=rank,
                retrieval_method=f"dense_{self.collection_name}"
            ))
        return results

def compute_rrf(bm25_res: List[SearchResult], dense_res: List[SearchResult], k: int = 60, top_k: int = 4) -> List[SearchResult]:
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, SearchResult] = {}
    b_ranks: Dict[str, int] = {}
    d_ranks: Dict[str, int] = {}

    for r, res in enumerate(bm25_res, 1):
        cid = res.chunk_id
        b_ranks[cid] = r
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (0.5 / (k + r))
        chunk_map[cid] = res

    for r, res in enumerate(dense_res, 1):
        cid = res.chunk_id
        d_ranks[cid] = r
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (0.5 / (k + r))
        if cid not in chunk_map:
            chunk_map[cid] = res

    sorted_cids = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)[:top_k]
    hybrid_results = []
    for cid in sorted_cids:
        base = chunk_map[cid]
        hybrid_results.append(SearchResult(
            chunk_id=base.chunk_id,
            document_name=base.document_name,
            document_number=base.document_number,
            chapter=base.chapter,
            article=base.article,
            clause=base.clause,
            point=base.point,
            page_start=base.page_start,
            page_end=base.page_end,
            text=base.text,
            score=rrf_scores[cid],
            bm25_rank=b_ranks.get(cid),
            dense_rank=d_ranks.get(cid),
            retrieval_method="hybrid_rrf"
        ))
    return hybrid_results

def expand_parent_child(primary_chunks: List[SearchResult], article_index: Dict[str, List[Dict[str, Any]]], max_siblings: int = MAX_PARENT_CHILD_SIBLINGS) -> List[SearchResult]:
    all_chunks = list(primary_chunks)
    seen_cids = {c.chunk_id for c in primary_chunks}

    for p in primary_chunks:
        k = f"{p.document_number}|||{p.article.strip()}"
        siblings = article_index.get(k, [])
        added_count = 0
        for s in siblings:
            if s["chunk_id"] not in seen_cids:
                seen_cids.add(s["chunk_id"])
                all_chunks.append(SearchResult(
                    chunk_id=s["chunk_id"],
                    document_name=s["document_name"],
                    document_number=s["document_number"],
                    chapter=s["chapter"],
                    article=s["article"],
                    clause=s["clause"],
                    point=s.get("point"),
                    page_start=s["page_start"],
                    page_end=s["page_end"],
                    text=s["text"],
                    score=p.score * 0.9,
                    retrieval_method="parent_child_expansion"
                ))
                added_count += 1
                if added_count >= max_siblings:
                    break
    return all_chunks

def calc_stats(ranks: List[int]) -> Dict[str, float]:
    total = len(ranks)
    h1 = sum(1 for r in ranks if r == 1) / total * 100
    h3 = sum(1 for r in ranks if 1 <= r <= 3) / total * 100
    h5 = sum(1 for r in ranks if 1 <= r <= 5) / total * 100
    mrr5 = sum((1.0 / r) if 1 <= r <= 5 else 0.0 for r in ranks) / total
    return {"Hit@1": round(h1, 2), "Hit@3": round(h3, 2), "Hit@5": round(h5, 2), "MRR@5": round(mrr5, 4)}

def is_target_match(target_doc: str, target_art: str, doc_num: str, chunk_art: str) -> bool:
    if target_doc not in doc_num:
        return False
    clean_target = target_art.strip().rstrip(".")
    pattern = rf"^{re.escape(clean_target)}(\.|\s|$)"
    return bool(re.search(pattern, chunk_art.strip())) or (clean_target in chunk_art)

def run_ablation():
    proc = psutil.Process(os.getpid())
    ram_init = proc.memory_info().rss / (1024 * 1024)

    logger.info("=== BẮT ĐẦU ABLATION STUDY PHASE 4.2 ===")

    # 1. Load Benchmarks
    bench_file = ROOT_DIR / "data" / "benchmark" / "gold_standard_benchmark_canonical.json"
    with open(bench_file, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    # 2. Build sibling index for parent-child
    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        all_chunks_raw = json.load(f)
    article_index = {}
    for c in all_chunks_raw:
        k = f"{c['document_number']}|||{c['article'].strip()}"
        if k not in article_index:
            article_index[k] = []
        article_index[k].append(c)

    # 3. Load 4 searchers
    # BM25 V1
    bm25_v1 = BM25Searcher(BM25_INDEX_PATH)
    bm25_v1.load_index()
    # BM25 V2
    bm25_v2 = BM25NgramSearcher(BM25_NGRAM_INDEX_PATH)
    bm25_v2.load_index()
    # Dense V1 (MiniLM-L6 English)
    dense_v1 = DirectDenseSearcher("sentence-transformers/all-MiniLM-L6-v2", "vietnamese_legal_documents")
    # Dense V2 (Multilingual MiniLM-L12)
    dense_v2 = DirectDenseSearcher("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "vietnamese_legal_multilingual")

    ram_loaded = proc.memory_info().rss / (1024 * 1024)
    logger.info(f"RAM sau khi nạp đủ 4 searchers: {ram_loaded:.2f} MB (Delta: {ram_loaded - ram_init:+.2f} MB)")

    # 4. Dense Alone Evaluation (Recall@5, 10, 20 & Hit rates)
    print("\n" + "=" * 100)
    print("PHẦN 1: ĐÁNH GIÁ ĐỘC LẬP DENSE V1 (ENGLISH) vs DENSE V2 (MULTILINGUAL)")
    print("=" * 100)

    for dense_name, d_searcher in [("Dense V1 (all-MiniLM-L6-v2)", dense_v1), ("Dense V2 (multilingual-MiniLM-L12)", dense_v2)]:
        art_ranks = []
        cl_ranks = []
        rec_5 = 0
        rec_10 = 0
        rec_20 = 0
        latencies = []

        for item in benchmarks:
            q = item["query"]
            tdoc = item["target_document"]
            tart = item["target_article"].strip().rstrip(".")
            tclauses = item["target_clauses"]

            t0 = time.time()
            hits = d_searcher.search(q, top_k=20)
            latencies.append((time.time() - t0) * 1000)

            a_r = 999
            c_r = 999
            for r, h in enumerate(hits, 1):
                if is_target_match(tdoc, tart, h.document_number, h.article):
                    if a_r == 999: a_r = r
                    for tc in tclauses:
                        if tc in h.clause and c_r == 999:
                            c_r = r
            art_ranks.append(a_r)
            cl_ranks.append(c_r)

            if c_r <= 5: rec_5 += 1
            if c_r <= 10: rec_10 += 1
            if c_r <= 20: rec_20 += 1

        total = len(benchmarks)
        print(f"\n--- {dense_name} ---")
        m_a = calc_stats(art_ranks)
        m_c = calc_stats(cl_ranks)
        print(f"Article: Hit@1={m_a['Hit@1']}%, Hit@3={m_a['Hit@3']}%, Hit@5={m_a['Hit@5']}%, MRR@5={m_a['MRR@5']}")
        print(f"Clause:  Hit@1={m_c['Hit@1']}%, Hit@3={m_c['Hit@3']}%, Hit@5={m_c['Hit@5']}%, MRR@5={m_c['MRR@5']}")
        print(f"Clause Recall: @5={rec_5}/{total} ({rec_5/total*100:.1f}%), @10={rec_10}/{total} ({rec_10/total*100:.1f}%), @20={rec_20}/{total} ({rec_20/total*100:.1f}%)")
        print(f"Độ trễ trung bình: {sum(latencies)/len(latencies):.2f} ms")

    # 5. Hybrid 4-Configuration Ablation Study
    print("\n" + "=" * 100)
    print("PHẦN 2: ĐỐI SÁNH 4 CẤU HÌNH HYBRID FUSION (Pool=15, Top-K=4, RRF_K=60)")
    print("=" * 100)

    configs = [
        ("A: BM25_V1 + Dense_V1", bm25_v1, dense_v1),
        ("B: BM25_V2 + Dense_V1", bm25_v2, dense_v1),
        ("C: BM25_V1 + Dense_V2", bm25_v1, dense_v2),
        ("D: BM25_V2 + Dense_V2", bm25_v2, dense_v2)
    ]

    all_config_results = {}

    for cfg_name, b_searcher, d_searcher in configs:
        prim_art_ranks = []
        prim_cl_ranks = []
        full_art_hits = 0
        full_cl_hits = 0
        full_all_cl_hits = 0
        latencies = []
        q_ranks_map = {}

        for item in benchmarks:
            qid = item["id"]
            q = item["query"]
            tdoc = item["target_document"]
            tart = item["target_article"].strip().rstrip(".")
            tclauses = item["target_clauses"]

            t0 = time.time()
            b_hits = b_searcher.search(q, top_k=15)
            d_hits = d_searcher.search(q, top_k=15)
            primary_hits = compute_rrf(b_hits, d_hits, k=RRF_K, top_k=4)
            lat = (time.time() - t0) * 1000
            latencies.append(lat)

            # Evaluate Primary Top-4
            pa_r = 999
            pc_r = 999
            for r, h in enumerate(primary_hits, 1):
                if is_target_match(tdoc, tart, h.document_number, h.article):
                    if pa_r == 999: pa_r = r
                    for tc in tclauses:
                        if tc in h.clause and pc_r == 999:
                            pc_r = r
            prim_art_ranks.append(pa_r)
            prim_cl_ranks.append(pc_r)
            q_ranks_map[qid] = {"primary_art_rank": pa_r, "primary_cl_rank": pc_r}

            # Evaluate After Parent-Child Expansion
            all_chunks = expand_parent_child(primary_hits, article_index)
            has_full_art = False
            found_clauses = set()
            for h in all_chunks:
                if is_target_match(tdoc, tart, h.document_number, h.article):
                    has_full_art = True
                    for tc in tclauses:
                        if tc in h.clause:
                            found_clauses.add(tc)
            if has_full_art: full_art_hits += 1
            if len(found_clauses) > 0: full_cl_hits += 1
            if len(found_clauses) == len(tclauses): full_all_cl_hits += 1

            q_ranks_map[qid]["expanded_art_hit"] = has_full_art
            q_ranks_map[qid]["expanded_cl_hit"] = len(found_clauses) > 0
            q_ranks_map[qid]["expanded_all_cl_hit"] = len(found_clauses) == len(tclauses)

        stats_art = calc_stats(prim_art_ranks)
        stats_cl = calc_stats(prim_cl_ranks)
        total = len(benchmarks)

        all_config_results[cfg_name] = {
            "primary_article": stats_art,
            "primary_clause": stats_cl,
            "expanded_article_hits": f"{full_art_hits}/{total} ({full_art_hits/total*100:.1f}%)",
            "expanded_clause_hits": f"{full_cl_hits}/{total} ({full_cl_hits/total*100:.1f}%)",
            "expanded_all_clause_hits": f"{full_all_cl_hits}/{total} ({full_all_cl_hits/total*100:.1f}%)",
            "avg_latency_ms": round(sum(latencies)/len(latencies), 2),
            "per_question": q_ranks_map
        }

    # Print Summary Table
    print(f"\n{'Cấu hình Hybrid':<28} | {'Primary Art Hit@1':<18} | {'Primary Cl Hit@1':<18} | {'Expanded Cl Hit':<18} | {'Độ trễ':<10}")
    print("-" * 100)
    for cfg_name, res in all_config_results.items():
        print(f"{cfg_name:<28} | {res['primary_article']['Hit@1']:<18.2f}% | {res['primary_clause']['Hit@1']:<18.2f}% | {res['expanded_clause_hits']:<18} | {res['avg_latency_ms']:<7.2f} ms")

    # Detailed Per-Question Tracking across 4 configurations
    print("\n" + "=" * 100)
    print("THEO DÕI THỨ HẠNG CẤP KHOẢN (PRIMARY TOP-4) CỦA 16 CÂU HỎI QUA 4 CẤU HÌNH")
    print("=" * 100)
    print(f"{'QID':<4} | {'Target':<22} | {'Cfg A (V1+V1)':<14} | {'Cfg B (V2+V1)':<14} | {'Cfg C (V1+V2)':<14} | {'Cfg D (V2+V2)':<14}")
    print("-" * 100)
    for item in benchmarks:
        qid = item["id"]
        tgt = f"{item['target_article']} {item['target_clauses']}"
        rA = all_config_results["A: BM25_V1 + Dense_V1"]["per_question"][qid]["primary_cl_rank"]
        rB = all_config_results["B: BM25_V2 + Dense_V1"]["per_question"][qid]["primary_cl_rank"]
        rC = all_config_results["C: BM25_V1 + Dense_V2"]["per_question"][qid]["primary_cl_rank"]
        rD = all_config_results["D: BM25_V2 + Dense_V2"]["per_question"][qid]["primary_cl_rank"]
        fmt = lambda r: str(r) if r <= 4 else "-"
        print(f"{qid:<4} | {tgt:<22} | {fmt(rA):<14} | {fmt(rB):<14} | {fmt(rC):<14} | {fmt(rD):<14}")

    # Track Q7, Q13, Q15, Q16
    print("\n" + "=" * 100)
    print("THEO DÕI ĐẶC BIỆT 4 CÂU HỎI TRỌNG TÂM: Q7, Q13, Q15, Q16")
    print("=" * 100)
    for qid in ["Q7", "Q13", "Q15", "Q16"]:
        item = next(b for b in benchmarks if b["id"] == qid)
        tgt = f"{item['target_article']} {item['target_clauses']}"
        expA = all_config_results["A: BM25_V1 + Dense_V1"]["per_question"][qid]["expanded_cl_hit"]
        expD = all_config_results["D: BM25_V2 + Dense_V2"]["per_question"][qid]["expanded_cl_hit"]
        rA = all_config_results["A: BM25_V1 + Dense_V1"]["per_question"][qid]["primary_cl_rank"]
        rD = all_config_results["D: BM25_V2 + Dense_V2"]["per_question"][qid]["primary_cl_rank"]
        print(f"[{qid}] {tgt:<25} | Cfg A: Prim Cl Rank {rA if rA<=4 else '-'}, P-C Hit: {expA}  ==>  Cfg D: Prim Cl Rank {rD if rD<=4 else '-'}, P-C Hit: {expD}")

    # Save to JSON report
    out_file = ROOT_DIR / "reports" / "audit_phase4_2_multilingual_ablation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_config_results, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu toàn bộ kết quả Ablation Study vào: {out_file}")

if __name__ == "__main__":
    run_ablation()
