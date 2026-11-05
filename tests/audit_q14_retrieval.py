import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.intent_agent import IntentAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever
from src.retrieval.embedding import LegalEmbeddingModel
from config import BM25_INDEX_PATH

def audit_q14():
    print("="*90)
    print("KIỂM TOÁN CHI TIẾT CÂU HỎI Q14 - KIỂM TRA HYBRID GỐC VÀ PARENT-CHILD EXPANSION")
    print("="*90)

    raw_query = "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
    intent_agent = IntentAgent()
    intent_res = intent_agent.classify_intent(raw_query)

    print(f"Câu hỏi gốc: '{raw_query}'")
    print(f"Lĩnh vực:    {intent_res.domain}")
    print(f"Từ khóa mở rộng: {intent_res.extracted_keywords}")
    print(f"Câu hỏi mở rộng: '{intent_res.expanded_query}'")

    bm25 = BM25Searcher(BM25_INDEX_PATH)
    bm25.load_index()
    emb = LegalEmbeddingModel()
    dense = DenseVectorSearcher(emb)
    retriever = HybridLegalRetriever(bm25, dense)

    # 1. Inspect without expansion for both raw_query and expanded_query
    for q_type, q in [("CÂU HỎI GỐC (RAW QUERY)", raw_query), ("CÂU HỎI MỞ RỘNG (EXPANDED QUERY)", intent_res.expanded_query)]:
        print("\n" + "-"*85)
        print(f"--- THỰC THI TRUY XUẤT CHO: {q_type} ---")
        print(f"Query string: '{q}'")

        # BM25 Top 5
        bm25_hits = bm25.search(q, top_k=5)
        print("1. BM25 TOP 5:")
        for r in bm25_hits:
            has_75 = "75%" in r.text
            print(f"   [Rank {r.bm25_rank}] Score: {r.score:6.3f} | {r.document_number} | {r.article} | {r.clause} (ID: {r.chunk_id}) | Has 75%: {has_75}")

        # Dense Top 5
        dense_hits = dense.search(q, top_k=5)
        print("2. DENSE VECTOR TOP 5:")
        for r in dense_hits:
            has_75 = "75%" in r.text
            print(f"   [Rank {r.dense_rank}] Score: {r.score:6.3f} | {r.document_number} | {r.article} | {r.clause} (ID: {r.chunk_id}) | Has 75%: {has_75}")

        # Hybrid RRF Top 5
        hybrid_hits = retriever.search(q, top_k=5, candidate_pool=20)
        print("3. HYBRID RRF TOP 5:")
        for rank, r in enumerate(hybrid_hits, 1):
            has_75 = "75%" in r.text
            ranks_str = f"BM25 R{r.bm25_rank or '-'}/Dense R{r.dense_rank or '-'}"
            print(f"   [Rank {rank}] Score: {r.score:.5f} ({ranks_str:18}) | {r.document_number} | {r.article} | {r.clause} (ID: {r.chunk_id}) | Has 75%: {has_75}")

    # 2. Inspect RetrievalAgent with Parent-Child Expansion
    retrieval_agent = RetrievalAgent(retriever)
    ret_ctx = retrieval_agent.retrieve(intent_res.normalized_query, intent_res.expanded_query, top_k=4)

    print("\n" + "="*85)
    print("--- KIỂM TRA DANH SÁCH CHUNKS TRƯỚC VÀ SAU PARENT-CHILD EXPANSION ---")
    print(f"Tổng chunks Primary (Trước expansion): {len(ret_ctx.primary_chunks)}")
    print(f"Tổng chunks Expanded (Được bổ sung):   {len(ret_ctx.expanded_chunks)}")
    print(f"Tổng chunks Toàn bộ (Sau expansion):   {len(ret_ctx.all_chunks)}")

    print("\nA. DANH SÁCH CHUNKS TRƯỚC EXPANSION (PRIMARY CHUNKS):")
    primary_has_khoan_2 = False
    for idx, c in enumerate(ret_ctx.primary_chunks, 1):
        has_75 = "75%" in c.text
        is_k2_d45 = "Điều 45." in c.article and "Khoản 2" in c.clause
        if is_k2_d45:
            primary_has_khoan_2 = True
        print(f"   [{idx}] {c.document_number} | {c.article} | {c.clause} (ID: {c.chunk_id}) | Score: {c.score:.5f} | K2_D45: {is_k2_d45} | 75%: {has_75}")

    print("\nB. DANH SÁCH CHUNKS ĐƯỢC BỔ SUNG BỞI PARENT-CHILD EXPANSION:")
    expanded_has_khoan_2 = False
    for idx, c in enumerate(ret_ctx.expanded_chunks, 1):
        has_75 = "75%" in c.text
        is_k2_d45 = "Điều 45." in c.article and "Khoản 2" in c.clause
        if is_k2_d45:
            expanded_has_khoan_2 = True
        print(f"   [+ {idx}] {c.document_number} | {c.article} | {c.clause} (ID: {c.chunk_id}) | Score: {c.score:.5f} | K2_D45: {is_k2_d45} | 75%: {has_75}")

    print("\n" + "="*85)
    print("KẾT LUẬN KIỂM TOÁN Q14:")
    print(f"1. Khoản 2 Điều 45 có trong Primary Hits (Trước expansion) không?: {primary_has_khoan_2}")
    print(f"2. Khoản 2 Điều 45 có được bổ sung qua Parent-Child Expansion không?: {expanded_has_khoan_2}")
    print(f"3. Khoản 2 Điều 45 có mặt trong Context gửi cho LLM không?:         {primary_has_khoan_2 or expanded_has_khoan_2}")
    print("="*85)

if __name__ == "__main__":
    audit_q14()
