import sys
import json
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import CHUNKS_JSON_PATH, BM25_INDEX_PATH
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever
from src.retrieval.embedding import LegalEmbeddingModel
from src.utils.logger import get_logger

logger = get_logger("TestRetrieval")

# 16 Benchmark Questions
TEST_QUERIES = [
    # Nhóm 1: Hợp đồng lao động
    {
        "id": "Q1",
        "category": "Hợp đồng lao động",
        "query": "Hợp đồng lao động có những loại nào?",
        "expected_keywords": ["loại hợp đồng", "không xác định thời hạn", "xác định thời hạn", "Điều 20"]
    },
    {
        "id": "Q2",
        "category": "Hợp đồng lao động & Thử việc",
        "query": "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?",
        "expected_keywords": ["thử việc", "thời gian thử việc", "Điều 25", "60 ngày", "30 ngày"]
    },

    # Nhóm 2: Thời giờ làm việc và nghỉ ngơi
    {
        "id": "Q3",
        "category": "Thời giờ nghỉ ngơi",
        "query": "Người lao động được nghỉ phép hàng năm bao nhiêu ngày trong điều kiện bình thường?",
        "expected_keywords": ["nghỉ hằng năm", "nghỉ phép", "12 ngày làm việc", "Điều 113"]
    },
    {
        "id": "Q4",
        "category": "Thời giờ làm việc",
        "query": "Thời giờ làm việc bình thường không quá bao nhiêu giờ trong một ngày và một tuần?",
        "expected_keywords": ["thời giờ làm việc bình thường", "8 giờ", "48 giờ", "Điều 105"]
    },

    # Nhóm 3: Tiền lương
    {
        "id": "Q5",
        "category": "Tiền lương làm thêm giờ",
        "query": "Làm thêm giờ vào ngày nghỉ hàng tuần được trả lương tính như thế nào?",
        "expected_keywords": ["tiền lương làm thêm giờ", "ngày nghỉ hằng tuần", "200%", "Điều 98"]
    },
    {
        "id": "Q6",
        "category": "Tiền lương ngừng việc",
        "query": "Người sử dụng lao động có phải trả lương khi người lao động phải ngừng việc do lỗi của người sử dụng lao động không?",
        "expected_keywords": ["tiền lương ngừng việc", "ngừng việc", "Điều 99"]
    },

    # Nhóm 4: Chấm dứt hợp đồng lao động
    {
        "id": "Q7",
        "category": "Chấm dứt hợp đồng lao động",
        "query": "Người lao động có quyền đơn phương chấm dứt hợp đồng lao động không cần báo trước trong những trường hợp nào?",
        "expected_keywords": ["đơn phương chấm dứt hợp đồng", "không cần báo trước", "Điều 35"]
    },
    {
        "id": "Q8",
        "category": "Chấm dứt hợp đồng lao động",
        "query": "Trường hợp nào người sử dụng lao động không được thực hiện quyền đơn phương chấm dứt hợp đồng lao động?",
        "expected_keywords": ["không được thực hiện quyền đơn phương chấm dứt", "nghỉ ốm đau", "thai sản", "Điều 37"]
    },
    {
        "id": "Q9",
        "category": "Trách nhiệm chấm dứt HĐ",
        "query": "Trách nhiệm của người sử dụng lao động khi chấm dứt hợp đồng lao động gồm những gì?",
        "expected_keywords": ["trách nhiệm của người sử dụng lao động", "thanh toán", "chốt sổ", "Điều 48"]
    },

    # Nhóm 5: Bảo hiểm xã hội
    {
        "id": "Q10",
        "category": "Đối tượng tham gia BHXH",
        "query": "Những đối tượng người lao động nào thuộc diện tham gia bảo hiểm xã hội bắt buộc?",
        "expected_keywords": ["đối tượng tham gia", "bảo hiểm xã hội bắt buộc", "hợp đồng lao động", "Điều 2"]
    },
    {
        "id": "Q11",
        "category": "Chế độ thai sản",
        "query": "Điều kiện hưởng chế độ thai sản khi sinh con đối với lao động nữ là gì?",
        "expected_keywords": ["chế độ thai sản", "lao động nữ sinh con", "đóng bảo hiểm xã hội từ đủ 6 tháng"]
    },
    {
        "id": "Q12",
        "category": "Chế độ thai sản",
        "query": "Thời gian nghỉ việc hưởng chế độ thai sản khi sinh một con là bao nhiêu tháng?",
        "expected_keywords": ["thời gian hưởng chế độ thai sản", "sinh con", "06 tháng"]
    },
    {
        "id": "Q13",
        "category": "Chế độ ốm đau",
        "query": "Điều kiện hưởng chế độ ốm đau đối với người lao động tham gia bảo hiểm xã hội bắt buộc là gì?",
        "expected_keywords": ["chế độ ốm đau", "bị ốm đau, tai nạn"]
    },
    {
        "id": "Q14",
        "category": "Chế độ ốm đau",
        "query": "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?",
        "expected_keywords": ["mức hưởng chế độ ốm đau", "75%"]
    },
    {
        "id": "Q15",
        "category": "Hưu trí",
        "query": "Điều kiện hưởng lương hưu và tuổi nghỉ hưu của người lao động được quy định như thế nào?",
        "expected_keywords": ["lương hưu", "tuổi nghỉ hưu", "hưu trí"]
    },

    # Nhóm 6: Câu hỏi có cách diễn đạt đời thường / khác văn bản luật
    {
        "id": "Q16",
        "category": "Diễn đạt đời thường",
        "query": "Nghỉ đẻ thì công ty có phải trả lương hay bảo hiểm xã hội chi trả?",
        "expected_keywords": ["thai sản", "tiền lương", "bảo hiểm xã hội chi trả"]
    }
]

def run_retrieval_benchmark():
    print("Khởi tạo hệ thống tìm kiếm BM25, Dense Vector và Hybrid Search...")

    # Load BM25
    bm25_searcher = BM25Searcher(BM25_INDEX_PATH)
    if not bm25_searcher.load_index():
        logger.error("Chưa xây dựng chỉ mục BM25! Vui lòng chạy build_vector_db.py trước.")
        return

    # Load Dense Vector
    emb_model = LegalEmbeddingModel()
    dense_searcher = DenseVectorSearcher(emb_model)

    # Hybrid Retriever
    hybrid_retriever = HybridLegalRetriever(bm25_searcher, dense_searcher)

    print("\n" + "="*80)
    print("BẮT ĐẦU KIỂM THỬ TRUY XUẤT PHÁP LUẬT (BENCHMARK 16 CÂU HỎI)")
    print("="*80)

    total_relevant = 0

    for item in TEST_QUERIES:
        qid = item["id"]
        cat = item["category"]
        query = item["query"]

        print(f"\n--------------------------------------------------------------------------------")
        print(f"[{qid}] [{cat}] CÂU HỎI: \"{query}\"")
        print(f"Từ khóa căn cứ mong đợi: {item['expected_keywords']}")

        # Retrieve Top 5
        bm25_res = bm25_searcher.search(query, top_k=5)
        dense_res = dense_searcher.search(query, top_k=5)
        hybrid_res = hybrid_retriever.search(query, top_k=5)

        # Print Comparison Summary
        print("\n  >> TOP 5 BM25:")
        for r in bm25_res:
            print(f"     [R{r.bm25_rank}] Score: {r.score:.3f} | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")

        print("\n  >> TOP 5 DENSE SEARCH:")
        for r in dense_res:
            print(f"     [R{r.dense_rank}] Score: {r.score:.3f} | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")

        print("\n  >> TOP 5 HYBRID SEARCH (RRF):")
        top_hybrid = hybrid_res[0] if hybrid_res else None
        is_relevant = False
        for r in hybrid_res:
            ranks_str = f"BM25 R{r.bm25_rank or '-'}/Dense R{r.dense_rank or '-'}"
            print(f"     Score: {r.score:.4f} ({ranks_str}) | {r.document_name} | {r.article} | {r.clause} (Trang {r.page_start})")
            # Check relevance
            comb_text = (r.article + " " + r.text).lower()
            if any(k.lower() in comb_text for k in item["expected_keywords"]):
                is_relevant = True

        if is_relevant:
            total_relevant += 1
            print("  ==> ĐÁNH GIÁ CHẤT LƯỢNG: ĐẠT (Tìm thấy đúng căn cứ pháp luật)")
        else:
            print("  ==> ĐÁNH GIÁ CHẤT LƯỢNG: CẦN CẢI THIỆN")

        if top_hybrid:
            print(f"\n  NỘI DUNG CHUNK TOP 1 HYBRID:")
            snippet = top_hybrid.text.replace("\n", " ")
            print(f"  \"{snippet[:250]}...\"")

    print("\n" + "="*80)
    print(f"TỔNG KẾT KIỂM THỬ RETRIEVAL: {total_relevant}/{len(TEST_QUERIES)} câu tìm thấy căn cứ chính xác ({total_relevant/len(TEST_QUERIES)*100:.1f}%)")
    print("="*80)

if __name__ == "__main__":
    run_retrieval_benchmark()
