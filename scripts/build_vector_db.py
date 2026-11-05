import json
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import CHUNKS_JSON_PATH, BM25_INDEX_PATH, VECTOR_DB_DIR
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher
from src.retrieval.embedding import LegalEmbeddingModel
from src.utils.logger import get_logger

logger = get_logger("BuildVectorDB")

def build_retrieval_indices(force_rebuild: bool = False):
    if not CHUNKS_JSON_PATH.exists():
        logger.info(f"Không tìm thấy {CHUNKS_JSON_PATH}. Bắt đầu chạy xử lý tài liệu trước...")
        from scripts.process_documents import run_document_processing
        run_document_processing()

    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logger.info(f"Đã nạp {len(chunks)} chunks pháp luật.")

    # 1. Build / Load BM25 Index
    bm25_searcher = BM25Searcher(BM25_INDEX_PATH)
    if force_rebuild or not BM25_INDEX_PATH.exists():
        logger.info("Bắt đầu xây dựng chỉ mục BM25...")
        bm25_searcher.build_index(chunks)
    else:
        logger.info("Chỉ mục BM25 đã tồn tại, kiểm tra tải lại...")
        bm25_searcher.load_index()

    # 2. Build / Check ChromaDB Vector Collection
    embedding_model = LegalEmbeddingModel()
    dense_searcher = DenseVectorSearcher(embedding_model)

    current_count = dense_searcher.count()
    logger.info(f"Số lượng vectors hiện có trong ChromaDB: {current_count}")

    if force_rebuild or current_count < len(chunks):
        logger.info(f"Cần thêm vector mới vào ChromaDB (hiện có: {current_count}/{len(chunks)})...")
        dense_searcher.add_chunks(chunks)
    else:
        logger.info("ChromaDB đã được nạp đầy đủ vectors. Bỏ qua bước tạo lại vector để tiết kiệm tài nguyên!")

    logger.info("Hoàn tất thiết lập toàn bộ chỉ mục BM25 và Vector Database!")

if __name__ == "__main__":
    force = "--force" in sys.argv
    build_retrieval_indices(force_rebuild=force)
