import sys
import json
import time
import os
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil
from config import CHUNKS_JSON_PATH, PROCESSED_DATA_DIR
from src.retrieval.bm25_ngram import BM25NgramSearcher, BM25_NGRAM_INDEX_PATH
from src.utils.logger import get_logger

logger = get_logger("BuildBM25Ngram")

def build_bm25_ngram():
    process = psutil.Process(os.getpid())
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    logger.info("=== BẮT ĐẦU XÂY DỰNG BM25 N-GRAM INDEX (PHASE 4.1) ===")
    logger.info(f"RAM tiến trình trước khi nạp: {ram_before_mb:.2f} MB")

    if not CHUNKS_JSON_PATH.exists():
        logger.error(f"Không tìm thấy file chunks tại {CHUNKS_JSON_PATH}!")
        return

    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    logger.info(f"Đã nạp {len(chunks)} chunks.")

    t0 = time.time()
    searcher = BM25NgramSearcher(BM25_NGRAM_INDEX_PATH)
    searcher.build_index(chunks)
    build_time = time.time() - t0

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    file_size_kb = BM25_NGRAM_INDEX_PATH.stat().st_size / 1024

    logger.info(f"Hoàn thành xây dựng BM25 N-gram trong {build_time:.3f} giây!")
    logger.info(f"Vị trí file lưu: {BM25_NGRAM_INDEX_PATH}")
    logger.info(f"Kích thước file: {file_size_kb:.2f} KB ({file_size_kb/1024:.2f} MB)")
    logger.info(f"RAM tiến trình sau khi index: {ram_after_mb:.2f} MB (Delta: {ram_after_mb - ram_before_mb:+.2f} MB)")

if __name__ == "__main__":
    build_bm25_ngram()
