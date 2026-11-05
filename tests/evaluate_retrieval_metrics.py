import sys
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import BM25_INDEX_PATH
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever
from src.retrieval.embedding import LegalEmbeddingModel

# Ground Truth Definition for the 16 Benchmark Questions
BENCHMARK_GROUND_TRUTH = [
    {
        "id": "Q1",
        "query": "Hợp đồng lao động có những loại nào?",
        "ground_truth_articles": ["Điều 20."]
    },
    {
        "id": "Q2",
        "query": "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?",
        "ground_truth_articles": ["Điều 25."]
    },
    {
        "id": "Q3",
        "query": "Người lao động được nghỉ phép hàng năm bao nhiêu ngày trong điều kiện bình thường?",
        "ground_truth_articles": ["Điều 113."]
    },
    {
        "id": "Q4",
        "query": "Thời giờ làm việc bình thường không quá bao nhiêu giờ trong một ngày và một tuần?",
        "ground_truth_articles": ["Điều 105."]
    },
    {
        "id": "Q5",
        "query": "Làm thêm giờ vào ngày nghỉ hàng tuần được trả lương tính như thế nào?",
        "ground_truth_articles": ["Điều 98."]
    },
    {
        "id": "Q6",
        "query": "Người sử dụng lao động có phải trả lương khi người lao động phải ngừng việc do lỗi của người sử dụng lao động không?",
        "ground_truth_articles": ["Điều 99."]
    },
    {
        "id": "Q7",
        "query": "Người lao động có quyền đơn phương chấm dứt hợp đồng lao động không cần báo trước trong những trường hợp nào?",
        "ground_truth_articles": ["Điều 35."]
    },
    {
        "id": "Q8",
        "query": "Trường hợp nào người sử dụng lao động không được thực hiện quyền đơn phương chấm dứt hợp đồng lao động?",
        "ground_truth_articles": ["Điều 37."]
    },
    {
        "id": "Q9",
        "query": "Trách nhiệm của người sử dụng lao động khi chấm dứt hợp đồng lao động gồm những gì?",
        "ground_truth_articles": ["Điều 48."]
    },
    {
        "id": "Q10",
        "query": "Những đối tượng người lao động nào thuộc diện tham gia bảo hiểm xã hội bắt buộc?",
        "ground_truth_articles": ["Điều 2."]
    },
    {
        "id": "Q11",
        "query": "Điều kiện hưởng chế độ thai sản khi sinh con đối với lao động nữ là gì?",
        "ground_truth_articles": ["Điều 50."]
    },
    {
        "id": "Q12",
        "query": "Thời gian nghỉ việc hưởng chế độ thai sản khi sinh một con là bao nhiêu tháng?",
        "ground_truth_articles": ["Điều 53."]
    },
    {
        "id": "Q13",
        "query": "Điều kiện hưởng chế độ ốm đau đối với người lao động tham gia bảo hiểm xã hội bắt buộc là gì?",
        "ground_truth_articles": ["Điều 42."]
    },
    {
        "id": "Q14",
        "query": "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?",
        "ground_truth_articles": ["Điều 45."]
    },
    {
        "id": "Q15",
        "query": "Điều kiện hưởng lương hưu và tuổi nghỉ hưu của người lao động được quy định như thế nào?",
        "ground_truth_articles": ["Điều 169.", "Điều 64."]
    },
    {
        "id": "Q16",
        "query": "Nghỉ đẻ thì công ty có phải trả lương hay bảo hiểm xã hội chi trả?",
        "ground_truth_articles": ["Điều 168.", "Điều 53.", "Điều 93."]
    }
]

def calculate_metrics(ranks: List[int]) -> Dict[str, float]:
    total = len(ranks)
    hit_1 = sum(1 for r in ranks if r == 1)
    hit_3 = sum(1 for r in ranks if 1 <= r <= 3)
    hit_5 = sum(1 for r in ranks if 1 <= r <= 5)
    mrr_5 = sum((1.0 / r) if 1 <= r <= 5 else 0.0 for r in ranks) / total

    return {
        "Hit@1": (hit_1 / total) * 100,
        "Hit@3": (hit_3 / total) * 100,
        "Hit@5": (hit_5 / total) * 100,
        "MRR@5": mrr_5
    }

def evaluate_all():
    # Load searchers
    bm25 = BM25Searcher(BM25_INDEX_PATH)
    bm25.load_index()

    emb = LegalEmbeddingModel()
    dense = DenseVectorSearcher(emb)
    hybrid = HybridLegalRetriever(bm25, dense)

    bm25_ranks = []
    dense_ranks = []
    hybrid_ranks = []

    detailed_rows = []

    for item in BENCHMARK_GROUND_TRUTH:
        qid = item["id"]
        q = item["query"]
        gt_arts = item["ground_truth_articles"]

        bm25_res = bm25.search(q, top_k=5)
        dense_res = dense.search(q, top_k=5)
        hybrid_res = hybrid.search(q, top_k=5)

        # Find first rank of ground truth
        def find_rank(res_list):
            for rank, r in enumerate(res_list, 1):
                if any(r.article.startswith(gt) for gt in gt_arts):
                    return rank
            return 999  # Not in top 5

        r_bm25 = find_rank(bm25_res)
        r_dense = find_rank(dense_res)
        r_hybrid = find_rank(hybrid_res)

        bm25_ranks.append(r_bm25)
        dense_ranks.append(r_dense)
        hybrid_ranks.append(r_hybrid)

        detailed_rows.append({
            "id": qid,
            "query": q,
            "ground_truth": ", ".join(gt_arts),
            "bm25_rank": r_bm25 if r_bm25 <= 5 else "-",
            "dense_rank": r_dense if r_dense <= 5 else "-",
            "hybrid_rank": r_hybrid if r_hybrid <= 5 else "-",
        })

    m_bm25 = calculate_metrics(bm25_ranks)
    m_dense = calculate_metrics(dense_ranks)
    m_hybrid = calculate_metrics(hybrid_ranks)

    print("\n" + "="*85)
    print("BẢNG ĐÁNH GIÁ CHI TIẾT THỨ HẠNG CĂN CỨ PHÁP LÝ (TOP 5)")
    print("="*85)
    print(f"{'Mã':<4} | {'Căn cứ chuẩn':<15} | {'BM25':<6} | {'Dense':<6} | {'Hybrid (RRF)':<12} | Câu hỏi")
    print("-" * 85)
    for row in detailed_rows:
        print(f"{row['id']:<4} | {row['ground_truth']:<15} | {str(row['bm25_rank']):<6} | {str(row['dense_rank']):<6} | {str(row['hybrid_rank']):<12} | {row['query'][:40]}...")

    print("\n" + "="*85)
    print("BẢNG SO SÁNH CHỈ SỐ RETRIEVAL: BM25 vs DENSE vs HYBRID SEARCH")
    print("="*85)
    print(f"{'Phương pháp':<18} | {'Hit@1 (%)':<10} | {'Hit@3 (%)':<10} | {'Hit@5 (%)':<10} | {'MRR@5':<10}")
    print("-" * 85)
    print(f"{'BM25 (Từ khóa)':<18} | {m_bm25['Hit@1']:<10.1f} | {m_bm25['Hit@3']:<10.1f} | {m_bm25['Hit@5']:<10.1f} | {m_bm25['MRR@5']:<10.3f}")
    print(f"{'Dense (Vector)':<18} | {m_dense['Hit@1']:<10.1f} | {m_dense['Hit@3']:<10.1f} | {m_dense['Hit@5']:<10.1f} | {m_dense['MRR@5']:<10.3f}")
    print(f"{'Hybrid Search (RRF)':<18} | {m_hybrid['Hit@1']:<10.1f} | {m_hybrid['Hit@3']:<10.1f} | {m_hybrid['Hit@5']:<10.1f} | {m_hybrid['MRR@5']:<10.3f}")
    print("="*85)

    # Save to JSON
    with open(ROOT_DIR / "data" / "processed" / "retrieval_metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "BM25": m_bm25,
                "Dense": m_dense,
                "Hybrid": m_hybrid
            },
            "queries": detailed_rows
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    evaluate_all()
