import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import (
    DOCUMENTS_CONFIG,
    CHUNKS_JSON_PATH,
    CHUNKS_STATS_PATH,
    CHUNK_MAX_LENGTH,
    CHUNK_MIN_LENGTH
)
from src.retrieval.document_loader import PDFDocumentLoader
from src.retrieval.chunking import LegalTextChunker
from src.utils.logger import get_logger

logger = get_logger("ProcessDocuments")

def run_document_processing():
    all_chunks = []
    all_stats = {}

    chunker = LegalTextChunker(
        max_chunk_length=CHUNK_MAX_LENGTH,
        min_chunk_length=CHUNK_MIN_LENGTH
    )

    for doc_key, cfg in DOCUMENTS_CONFIG.items():
        logger.info(f"--- ĐANG XỬ LÝ: {cfg['document_name']} ({cfg['document_number']}) ---")
        loader = PDFDocumentLoader(cfg)
        pages = loader.load()

        chunks, stats = chunker.chunk_document(pages)
        all_stats[doc_key] = stats

        for c in chunks:
            all_chunks.append(c.to_dict())

    # Save to JSON files
    CHUNKS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    with open(CHUNKS_STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    logger.info(f"Đã lưu thành công {len(all_chunks)} chunks vào {CHUNKS_JSON_PATH}")
    logger.info(f"Đã lưu thống kê vào {CHUNKS_STATS_PATH}")
    return all_chunks, all_stats

if __name__ == "__main__":
    run_document_processing()
