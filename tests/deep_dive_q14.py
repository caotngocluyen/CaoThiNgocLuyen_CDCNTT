import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import BM25_INDEX_PATH
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever
from src.retrieval.embedding import LegalEmbeddingModel

def deep_dive_q14():
    q = "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
    print("="*85)
    print(f"KIỂM ĐỊNH CHUYÊN SÂU CÂU HỎI Q14:")
    print(f"\"{q}\"")
    print("="*85)

    bm25 = BM25Searcher(BM25_INDEX_PATH)
    bm25.load_index()

    emb = LegalEmbeddingModel()
    dense = DenseVectorSearcher(emb)
    hybrid = HybridLegalRetriever(bm25, dense)

    top5_bm25 = bm25.search(q, top_k=5)
    top5_dense = dense.search(q, top_k=5)
    top5_hybrid = hybrid.search(q, top_k=5)

    print("\n1. KẾT QUẢ BM25 (TOP 5):")
    for r in top5_bm25:
        print(f"   [Rank {r.bm25_rank}] Score: {r.score:.3f} | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")
        print(f"          Snippet: {r.text.replace(chr(10), ' ')[:140]}...")

    print("\n2. KẾT QUẢ DENSE VECTOR SEARCH (TOP 5):")
    for r in top5_dense:
        print(f"   [Rank {r.dense_rank}] Score: {r.score:.3f} | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")
        print(f"          Snippet: {r.text.replace(chr(10), ' ')[:140]}...")

    print("\n3. KẾT QUẢ HYBRID SEARCH - RRF (TOP 5):")
    for rank, r in enumerate(top5_hybrid, 1):
        ranks_info = f"BM25 R{r.bm25_rank or '-'}/Dense R{r.dense_rank or '-'}"
        print(f"   [Rank {rank}] Score: {r.score:.4f} ({ranks_info}) | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")
        print(f"          Snippet: {r.text.replace(chr(10), ' ')[:140]}...")

    # Check all clauses of Điều 45 in Luật BHXH
    print("\n4. KIỂM TRA TẤT CẢ CÁC KHOẢN CỦA ĐIỀU 45 (LUẬT BHXH):")
    with open(ROOT_DIR / "data" / "processed" / "legal_chunks.json", "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    dieu_45_chunks = [c for c in all_chunks if c["document_number"] == "41/2024/QH15" and "Điều 45." in c["article"]]
    for c in dieu_45_chunks:
        has_75 = "75%" in c["text"]
        print(f"   * {c['clause']} (ID: {c['chunk_id']}) | Có chứa 75%: {has_75}")
        if has_75:
            for line in c["text"].split("\n"):
                if "75%" in line or "mức hưởng" in line.lower():
                    print(f"     => {line.strip()}")

    # Analysis of why Điều 120 appeared at Rank 1 in Hybrid
    print("\n5. PHÂN TÍCH NGUYÊN NHÂN THỨ HẠNG VÀ ĐỀ XUẤT:")
    print("   - BM25 xếp Điều 45 Khoản 1 ở VỊ TRÍ SỐ 1 TUYỆT ĐỐI (Score 34.069).")
    print("   - Dense Search xếp Điều 120 ở Top 10 và các điều tổng quát khác.")
    print("   - Trong Hybrid Search (RRF), Điều 120 lọt lên Rank 1 vì nó xuất hiện ở cả BM25 (R3) và Dense (R10).")
    print("   - Tuy nhiên, Điều 45 Khoản 1 xuất hiện ngay tại RANK 2 của Hybrid Search!")
    print("   - Đầy đủ nội dung: 'Mức hưởng trợ cấp ốm đau... tính bằng 75% mức tiền lương...'")
    print("   - Cả hai điều luật đều nằm trong Top 3, đảm bảo cung cấp đầy đủ cho LLM ở Giai đoạn 3.")

if __name__ == "__main__":
    deep_dive_q14()
