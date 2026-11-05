from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL_NAME, EMBEDDING_FALLBACK_MODEL
from src.utils.logger import get_logger

logger = get_logger("EmbeddingModel")

class LegalEmbeddingModel:
    """
    Manages local dense embedding for legal chunks and search queries.
    Runs on CPU without requiring GPU.
    """
    _instance = None

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Đang nạp mô hình Embedding cục bộ: {self.model_name}...")
            # Try local cache first for zero network delay
            try:
                self.model = SentenceTransformer(self.model_name, device="cpu", local_files_only=True)
            except Exception:
                self.model = SentenceTransformer(self.model_name, device="cpu")
            logger.info(f"Nạp mô hình Embedding thành công: {self.model_name}")
        except Exception as e:
            logger.warning(f"Không thể tải mô hình {self.model_name}: {e}. Chuyển sang mô hình dự phòng: {EMBEDDING_FALLBACK_MODEL}")
            try:
                self.model_name = EMBEDDING_FALLBACK_MODEL
                self.model = SentenceTransformer(self.model_name, device="cpu")
                logger.info(f"Nạp mô hình dự phòng thành công: {self.model_name}")
            except Exception as e2:
                logger.error(f"Lỗi nạp mô hình dự phòng: {e2}")
                raise e2

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """
        Generates dense vector embeddings for input texts.
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings

    def encode_query(self, query: str) -> List[float]:
        """
        Encodes a single query string for vector search.
        """
        emb = self.encode([query], show_progress=False)[0]
        return emb.tolist()
