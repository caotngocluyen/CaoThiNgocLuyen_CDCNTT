import sys
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil
from config import BM25_INDEX_PATH, CHUNKS_JSON_PATH
from src.retrieval.hybrid_search import BM25Searcher
from src.retrieval.bm25_ngram import BM25NgramSearcher, BM25_NGRAM_INDEX_PATH
from src.utils.logger import get_logger

logger = get_logger("AblationBM25")

def calculate_metrics(ranks: List[int]) -> Dict[str, float]:
    total = len(ranks)
    h1 = sum(1 for r in ranks if r == 1) / total * 100
    h3 = sum(1 for r in ranks if 1 <= r <= 3) / total * 100
    h5 = sum(1 for r in ranks if 1 <= r <= 5) / total * 100
    mrr5 = sum((1.0 / r) if 1 <= r <= 5 else 0.0 for r in ranks) / total
    return {
        "Hit@1": round(h1, 2),
        "Hit@3": round(h3, 2),
        "Hit@5": round(h5, 2),
        "MRR@5": round(mrr5, 4)
    }

def run_bm25_ablation():
    print("=" * 100)
    print("ABLATION STUDY: BM25 BASELINE (V1) vs BM25 N-GRAM & LEGAL COMPOUNDS (PHASE 4.1 V2)")
    print("=" * 100)

    # 1. Load benchmark dataset
    benchmark_path = ROOT_DIR / "data" / "benchmark" / "gold_standard_benchmark_canonical.json"
    if not benchmark_path.exists():
        benchmark_path = ROOT_DIR / "tests" / "gold_standard_benchmark.json"

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    # 2. Load both BM25 searchers
    bm25_v1 = BM25Searcher(BM25_INDEX_PATH)
    if not bm25_v1.load_index():
        raise RuntimeError("Không tìm thấy bm25_index.pkl!")

    bm25_v2 = BM25NgramSearcher(BM25_NGRAM_INDEX_PATH)
    if not bm25_v2.load_index():
        raise RuntimeError("Không tìm thấy bm25_index_ngram.pkl!")

    # 3. Evaluate both
    rows = []
    v1_art_ranks = []
    v1_cl_ranks = []
    v2_art_ranks = []
    v2_cl_ranks = []

    v1_latencies = []
    v2_latencies = []

    for item in benchmarks:
        qid = item["id"]
        q = item["query"]
        target_doc = item["target_document"]
        target_art = item["target_article"].strip().rstrip(".")
        target_clauses = item["target_clauses"]

        # Search V1
        t0 = time.time()
        hits_v1 = bm25_v1.search(q, top_k=20)
        lat_v1 = (time.time() - t0) * 1000
        v1_latencies.append(lat_v1)

        # Search V2
        t0 = time.time()
        hits_v2 = bm25_v2.search(q, top_k=20)
        lat_v2 = (time.time() - t0) * 1000
        v2_latencies.append(lat_v2)

        def eval_hits(hits):
            art_rank = 999
            cl_rank = 999
            for r, res in enumerate(hits, 1):
                doc_match = target_doc in res.document_number
                art_match = res.article.strip().startswith(target_art) or (target_art in res.article)
                if doc_match and art_match:
                    if art_rank == 999:
                        art_rank = r
                    for tc in target_clauses:
                        if tc in res.clause and cl_rank == 999:
                            cl_rank = r
            return art_rank, cl_rank

        a_r1, c_r1 = eval_hits(hits_v1)
        a_r2, c_r2 = eval_hits(hits_v2)

        v1_art_ranks.append(a_r1)
        v1_cl_ranks.append(c_r1)
        v2_art_ranks.append(a_r2)
        v2_cl_ranks.append(c_r2)

        # Determine delta status
        def get_delta_str(r1, r2):
            if r2 < r1:
                return f"CẢI THIỆN ({r1} -> {r2})"
            elif r2 > r1:
                return f"GIẢM ({r1} -> {r2})"
            else:
                return f"GIỮ NGUYÊN ({r1})"

        rows.append({
            "id": qid,
            "query": q,
            "target": f"{target_art} {target_clauses}",
            "v1_art_rank": a_r1 if a_r1 <= 20 else "-",
            "v2_art_rank": a_r2 if a_r2 <= 20 else "-",
            "v1_cl_rank": c_r1 if c_r1 <= 20 else "-",
            "v2_cl_rank": c_r2 if c_r2 <= 20 else "-",
            "cl_status": get_delta_str(c_r1 if c_r1 <= 20 else 999, c_r2 if c_r2 <= 20 else 999),
            "lat_v1_ms": round(lat_v1, 2),
            "lat_v2_ms": round(lat_v2, 2)
        })

    # 4. Compute Summary Metrics
    m_art_v1 = calculate_metrics(v1_art_ranks)
    m_art_v2 = calculate_metrics(v2_art_ranks)
    m_cl_v1 = calculate_metrics(v1_cl_ranks)
    m_cl_v2 = calculate_metrics(v2_cl_ranks)

    # Print Table
    print(f"\n{'ID':<4} | {'Mục tiêu':<25} | {'V1 Art':<7} | {'V2 Art':<7} | {'V1 Cl':<7} | {'V2 Cl':<7} | {'Trạng thái Khoản':<22}")
    print("-" * 95)
    for r in rows:
        print(f"{r['id']:<4} | {r['target']:<25} | {str(r['v1_art_rank']):<7} | {str(r['v2_art_rank']):<7} | {str(r['v1_cl_rank']):<7} | {str(r['v2_cl_rank']):<7} | {r['cl_status']:<22}")

    print("\n" + "=" * 95)
    print("BẢNG TỔNG HỢP CHỈ SỐ ARTICLE & CLAUSE LEVEL")
    print("=" * 95)
    print(f"{'Chỉ số':<22} | {'Baseline (V1)':<15} | {'Phase 4.1 N-gram (V2)':<22} | {'Độ chênh lệch (Delta)':<18}")
    print("-" * 95)
    print(f"{'Article Hit@1 (%)':<22} | {m_art_v1['Hit@1']:<15.2f} | {m_art_v2['Hit@1']:<22.2f} | {m_art_v2['Hit@1'] - m_art_v1['Hit@1']:+18.2f}%")
    print(f"{'Article Hit@3 (%)':<22} | {m_art_v1['Hit@3']:<15.2f} | {m_art_v2['Hit@3']:<22.2f} | {m_art_v2['Hit@3'] - m_art_v1['Hit@3']:+18.2f}%")
    print(f"{'Article Hit@5 (%)':<22} | {m_art_v1['Hit@5']:<15.2f} | {m_art_v2['Hit@5']:<22.2f} | {m_art_v2['Hit@5'] - m_art_v1['Hit@5']:+18.2f}%")
    print(f"{'Article MRR@5':<22} | {m_art_v1['MRR@5']:<15.4f} | {m_art_v2['MRR@5']:<22.4f} | {m_art_v2['MRR@5'] - m_art_v1['MRR@5']:+18.4f}")
    print("-" * 95)
    print(f"{'Clause Hit@1 (%)':<22} | {m_cl_v1['Hit@1']:<15.2f} | {m_cl_v2['Hit@1']:<22.2f} | {m_cl_v2['Hit@1'] - m_cl_v1['Hit@1']:+18.2f}%")
    print(f"{'Clause Hit@3 (%)':<22} | {m_cl_v1['Hit@3']:<15.2f} | {m_cl_v2['Hit@3']:<22.2f} | {m_cl_v2['Hit@3'] - m_cl_v1['Hit@3']:+18.2f}%")
    print(f"{'Clause Hit@5 (%)':<22} | {m_cl_v1['Hit@5']:<15.2f} | {m_cl_v2['Hit@5']:<22.2f} | {m_cl_v2['Hit@5'] - m_cl_v1['Hit@5']:+18.2f}%")
    print(f"{'Clause MRR@5':<22} | {m_cl_v1['MRR@5']:<15.4f} | {m_cl_v2['MRR@5']:<22.4f} | {m_cl_v2['MRR@5'] - m_cl_v1['MRR@5']:+18.4f}")
    print("-" * 95)
    print(f"{'Độ trễ trung bình (ms)':<22} | {sum(v1_latencies)/len(v1_latencies):<15.2f} | {sum(v2_latencies)/len(v2_latencies):<22.2f} | {sum(v2_latencies)/len(v2_latencies) - sum(v1_latencies)/len(v1_latencies):+18.2f} ms")

    # 5. Evaluate Focus Queries: Q1, Q7, Q13, Q15, Q16
    print("\n" + "=" * 95)
    print("THEO DÕI ĐẶC BIỆT 5 CÂU HỎI TRỌNG TÂM: Q1, Q7, Q13, Q15, Q16")
    print("=" * 95)
    focus_ids = ["Q1", "Q7", "Q13", "Q15", "Q16"]
    for r in rows:
        if r["id"] in focus_ids:
            print(f"[{r['id']}] {r['target']:<25} | V1: Art {r['v1_art_rank']}, Cl {r['v1_cl_rank']} -> V2: Art {r['v2_art_rank']}, Cl {r['v2_cl_rank']} | {r['cl_status']}")

    # 6. Save JSON report
    report_data = {
        "summary": {
            "v1": {
                "article": m_art_v1,
                "clause": m_cl_v1,
                "avg_latency_ms": round(sum(v1_latencies)/len(v1_latencies), 2)
            },
            "v2": {
                "article": m_art_v2,
                "clause": m_cl_v2,
                "avg_latency_ms": round(sum(v2_latencies)/len(v2_latencies), 2)
            },
            "deltas": {
                "article_hit1": round(m_art_v2['Hit@1'] - m_art_v1['Hit@1'], 2),
                "article_hit5": round(m_art_v2['Hit@5'] - m_art_v1['Hit@5'], 2),
                "article_mrr5": round(m_art_v2['MRR@5'] - m_art_v1['MRR@5'], 4),
                "clause_hit1": round(m_cl_v2['Hit@1'] - m_cl_v1['Hit@1'], 2),
                "clause_hit5": round(m_cl_v2['Hit@5'] - m_cl_v1['Hit@5'], 2),
                "clause_mrr5": round(m_cl_v2['MRR@5'] - m_cl_v1['MRR@5'], 4)
            }
        },
        "details": rows
    }

    report_path = ROOT_DIR / "reports" / "audit_phase4_1_bm25_ngram.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu kết quả kiểm thử vào: {report_path}")

if __name__ == "__main__":
    run_bm25_ablation()
