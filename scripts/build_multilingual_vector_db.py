import sys
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil
import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTOR_DB_DIR, CHUNKS_JSON_PATH
from src.utils.logger import get_logger

logger = get_logger("BuildMultilingualVectorDB")

MULTILINGUAL_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MULTILINGUAL_COLLECTION_NAME = "vietnamese_legal_multilingual"

def build_multilingual_collection(batch_size: int = 64):
    process = psutil.Process(os.getpid())
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    logger.info("=== BẮT ĐẦU XÂY DỰNG MULTILINGUAL VECTOR COLLECTION (PHASE 4.2) ===")
    logger.info(f"RAM tiến trình trước: {ram_before_mb:.2f} MB")

    # 1. Load Chunks
    if not CHUNKS_JSON_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file chunks tại {CHUNKS_JSON_PATH}!")

    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)

    total_chunks = len(chunks)
    logger.info(f"Đã nạp {total_chunks} chunks pháp luật.")

    # 2. Load Multilingual Model (Strict Offline)
    logger.info(f"Đang nạp mô hình Multilingual cục bộ: {MULTILINGUAL_MODEL_NAME} (local_files_only=True)...")
    t0_model = time.time()
    try:
        model = SentenceTransformer(MULTILINGUAL_MODEL_NAME, device="cpu", local_files_only=True)
    except Exception as e:
        logger.error(f"Lỗi nạp offline: {e}")
        raise e

    model_load_time = time.time() - t0_model
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"Nạp model thành công trong {model_load_time:.2f}s | Dim: {dim} | Device: {model.device}")

    # 3. Connect to Persistent ChromaDB
    chroma_path = str(VECTOR_DB_DIR / "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        name=MULTILINGUAL_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    existing_count = collection.count()
    logger.info(f"Số lượng vector hiện có trong collection '{MULTILINGUAL_COLLECTION_NAME}': {existing_count}")

    if existing_count == total_chunks:
        logger.info(f"Collection '{MULTILINGUAL_COLLECTION_NAME}' đã có đủ {total_chunks} vectors. Bỏ qua re-indexing!")
        ram_after_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(f"RAM hiện tại: {ram_after_mb:.2f} MB")
        return

    # 4. Generate Embeddings & Upsert in batches
    t0_index = time.time()
    logger.info(f"Bắt đầu encode và upsert {total_chunks} vectors vào '{MULTILINGUAL_COLLECTION_NAME}'...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i: i + batch_size]
        ids = [b["chunk_id"] for b in batch]
        documents = [b["text"] for b in batch]
        metadatas = [
            {
                "document_name": b["document_name"],
                "document_number": b["document_number"],
                "chapter": b["chapter"][:100],
                "article": b["article"][:100],
                "clause": b["clause"][:50],
                "point": b.get("point") or "",
                "page_start": int(b["page_start"]),
                "page_end": int(b["page_end"])
            }
            for b in batch
        ]

        # Normalize embeddings = True for cosine similarity
        embeddings = model.encode(
            documents,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"Đã lưu vector: {min(i + batch_size, total_chunks)}/{total_chunks} chunks")

    index_time = time.time() - t0_index
    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    logger.info("=== HOÀN TẤT THIẾT LẬP MULTILINGUAL VECTOR COLLECTION ===")
    logger.info(f"Thời gian encode & lưu: {index_time:.2f}s ({index_time/total_chunks*1000:.1f} ms/chunk)")
    logger.info(f"Tổng số vectors trong collection '{MULTILINGUAL_COLLECTION_NAME}': {collection.count()}")
    logger.info(f"RAM sau khi hoàn thành: {ram_after_mb:.2f} MB (Delta: {ram_after_mb - ram_before_mb:+.2f} MB)")

if __name__ == "__main__":
    build_multilingual_collection()
