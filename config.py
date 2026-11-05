import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OFFICIAL_DOCS_DIR = DATA_DIR / "official_documents"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
MODELS_DIR = BASE_DIR / "models"
LLM_DIR = MODELS_DIR / "llm"
EMBEDDING_DIR = MODELS_DIR / "embedding"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for d in [PROCESSED_DATA_DIR, VECTOR_DB_DIR, LLM_DIR, EMBEDDING_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Document Sources Configuration
DOCUMENTS_CONFIG = {
    "labor_code": {
        "file_path": OFFICIAL_DOCS_DIR / "labor_code" / "18-vbhn-vpqh.pdf",
        "document_name": "Bộ luật Lao động",
        "document_number": "18/VBHN-VPQH",
        "document_type": "Văn bản hợp nhất",
        "consolidation_date": "2026-02-12",
        "promulgation_date": "2019-11-20",
        "effective_date": "2021-01-01",
        "status": "Có hiệu lực",
        "domain": "labor",
        "note": "Xác thực theo VBHN số 18/VBHN-VPQH ngày 12/02/2026; văn bản gốc là Bộ luật Lao động số 45/2019/QH14 có hiệu lực từ 01/01/2021."
    },
    "social_insurance": {
        "file_path": OFFICIAL_DOCS_DIR / "social_insurance" / "41-2024-qh15.pdf",
        "document_name": "Luật Bảo hiểm xã hội",
        "document_number": "41/2024/QH15",
        "document_type": "Luật",
        "promulgation_date": "2024-06-29",
        "effective_date": "2025-07-01",
        "status": "Có hiệu lực từ 01/07/2025",
        "domain": "social_insurance",
        "note": "Luật Bảo hiểm xã hội số 41/2024/QH15 được Quốc hội khóa XV thông qua ngày 29/06/2024, có hiệu lực từ ngày 01/07/2025."
    }
}

# Processed Files
CHUNKS_JSON_PATH = PROCESSED_DATA_DIR / "legal_chunks.json"
CHUNKS_STATS_PATH = PROCESSED_DATA_DIR / "chunks_stats.json"
BM25_INDEX_PATH = PROCESSED_DATA_DIR / "bm25_index.pkl"

# Chunking Configuration
CHUNK_MAX_LENGTH = 1500  # Max characters per chunk before splitting long clauses
CHUNK_MIN_LENGTH = 30    # Ignore empty noise lines

# Embedding Model Configuration
# Light-weight, high performance local embedding model (runs 100% on CPU, cached locally)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_FALLBACK_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# Vector DB Configuration
CHROMA_COLLECTION_NAME = "vietnamese_legal_documents"

# Hybrid Search Configuration
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60
RRF_WEIGHT_BM25 = 0.5
RRF_WEIGHT_DENSE = 0.5
TOP_K_DEFAULT = 5

# Local LLM Configuration (Phase 3)
LLM_MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
LLM_MODEL_PATH = LLM_DIR / LLM_MODEL_FILENAME
LLM_N_CTX = 3072
LLM_N_THREADS = 6
LLM_TEMPERATURE = 0.1
LLM_TOP_P = 0.9
LLM_MAX_TOKENS = 650

# Agentic Orchestration Configuration
RETRIEVAL_TOP_K = 4
RETRIEVAL_CANDIDATE_POOL = 15
PARENT_CHILD_EXPAND = True
MAX_PARENT_CHILD_SIBLINGS = 5
MAX_RETRY_ATTEMPTS = 1

