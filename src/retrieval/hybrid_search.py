import re
import pickle
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings

from config import (
    VECTOR_DB_DIR,
    CHROMA_COLLECTION_NAME,
    BM25_INDEX_PATH,
    RRF_K,
    RRF_WEIGHT_BM25,
    RRF_WEIGHT_DENSE,
    TOP_K_DEFAULT
)
from src.retrieval.embedding import LegalEmbeddingModel
from src.utils.logger import get_logger

logger = get_logger("HybridSearch")

@dataclass
class SearchResult:
    chunk_id: str
    document_name: str
    document_number: str
    chapter: str
    article: str
    clause: str
    point: Optional[str]
    page_start: int
    page_end: int
    text: str
    score: float
    bm25_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    retrieval_method: str = "hybrid"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def tokenize_vietnamese_legal(text: str) -> List[str]:
    """
    Tokenizes Vietnamese legal text for BM25.
    Preserves legal keywords, numbers, roman numerals, and clause identifiers.
    """
    text = text.lower()
    # Normalize punctuation but retain hyphens/slashes in doc numbers
    tokens = re.findall(r"[\w\d/_\-]+", text)
    return [t for t in tokens if len(t) > 1 or t.isdigit()]


class BM25Searcher:
    """
    BM25 Searcher using rank_bm25 for lexical legal term matching.
    """
    def __init__(self, index_path=BM25_INDEX_PATH):
        self.index_path = index_path
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[Dict[str, Any]] = []

    def build_index(self, chunks: List[Dict[str, Any]]):
        logger.info(f"Đang xây dựng chỉ mục BM25 cho {len(chunks)} chunks...")
        self.chunks = chunks
        corpus = [tokenize_vietnamese_legal(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
        logger.info(f"Đã lưu BM25 index vào {self.index_path}")

    def load_index(self) -> bool:
        if not self.index_path.exists():
            return False
        logger.info(f"Đang nạp BM25 index từ {self.index_path}...")
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.chunks = data["chunks"]
        logger.info(f"Nạp BM25 index thành công ({len(self.chunks)} chunks)")
        return True

    def search(self, query: str, top_k: int = TOP_K_DEFAULT) -> List[SearchResult]:
        if not self.bm25:
            raise ValueError("BM25 index chưa được khởi tạo!")

        tokenized_query = tokenize_vietnamese_legal(query)
        if not tokenized_query:
            return []

        doc_scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            if doc_scores[idx] <= 0:
                continue
            c = self.chunks[idx]
            results.append(SearchResult(
                chunk_id=c["chunk_id"],
                document_name=c["document_name"],
                document_number=c["document_number"],
                chapter=c["chapter"],
                article=c["article"],
                clause=c["clause"],
                point=c.get("point"),
                page_start=c["page_start"],
                page_end=c["page_end"],
                text=c["text"],
                score=float(doc_scores[idx]),
                bm25_rank=rank,
                retrieval_method="bm25"
            ))
        return results


class DenseVectorSearcher:
    """
    Dense Semantic Searcher using ChromaDB persistent vector storage.
    """
    def __init__(self, embedding_model: LegalEmbeddingModel):
        self.embedding_model = embedding_model
        chroma_path = str(VECTOR_DB_DIR / "chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self.collection.count()

    def add_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 128):
        total = len(chunks)
        logger.info(f"Đang tạo vector embedding và lưu vào ChromaDB ({total} chunks)...")

        for i in range(0, total, batch_size):
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
            embeddings = self.embedding_model.encode(documents, batch_size=batch_size).tolist()

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Đã lưu vector: {min(i + batch_size, total)}/{total} chunks")

        logger.info(f"Hoàn thành lưu {total} chunks vào ChromaDB collection '{CHROMA_COLLECTION_NAME}'")

    def search(self, query: str, top_k: int = TOP_K_DEFAULT) -> List[SearchResult]:
        query_vector = self.embedding_model.encode_query(query)

        query_res = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        results = []
        if not query_res["ids"] or not query_res["ids"][0]:
            return results

        ids = query_res["ids"][0]
        docs = query_res["documents"][0]
        metas = query_res["metadatas"][0]
        distances = query_res["distances"][0]

        for rank, (chunk_id, doc_text, meta, dist) in enumerate(zip(ids, docs, metas, distances), 1):
            # Convert cosine distance to similarity score
            sim_score = max(0.0, 1.0 - dist)
            results.append(SearchResult(
                chunk_id=chunk_id,
                document_name=meta.get("document_name", ""),
                document_number=meta.get("document_number", ""),
                chapter=meta.get("chapter", ""),
                article=meta.get("article", ""),
                clause=meta.get("clause", ""),
                point=meta.get("point") if meta.get("point") else None,
                page_start=meta.get("page_start", 1),
                page_end=meta.get("page_end", 1),
                text=doc_text,
                score=sim_score,
                dense_rank=rank,
                retrieval_method="dense"
            ))
        return results


class HybridLegalRetriever:
    """
    Hybrid Legal Retriever combining BM25 (lexical) and ChromaDB (semantic)
    using Reciprocal Rank Fusion (RRF).
    """
    def __init__(
        self,
        bm25_searcher: BM25Searcher,
        dense_searcher: DenseVectorSearcher,
        k: int = RRF_K,
        w_bm25: float = RRF_WEIGHT_BM25,
        w_dense: float = RRF_WEIGHT_DENSE
    ):
        self.bm25_searcher = bm25_searcher
        self.dense_searcher = dense_searcher
        self.k = k
        self.w_bm25 = w_bm25
        self.w_dense = w_dense

    def search(self, query: str, top_k: int = TOP_K_DEFAULT, candidate_pool: int = 20) -> List[SearchResult]:
        """
        Executes hybrid search via Reciprocal Rank Fusion.
        """
        # 1. Retrieve candidates from both methods
        bm25_results = self.bm25_searcher.search(query, top_k=candidate_pool)
        dense_results = self.dense_searcher.search(query, top_k=candidate_pool)

        # 2. Compute RRF scores
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, SearchResult] = {}
        bm25_ranks: Dict[str, int] = {}
        dense_ranks: Dict[str, int] = {}

        for rank, res in enumerate(bm25_results, 1):
            cid = res.chunk_id
            bm25_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.w_bm25 / (self.k + rank))
            chunk_map[cid] = res

        for rank, res in enumerate(dense_results, 1):
            cid = res.chunk_id
            dense_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.w_dense / (self.k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = res

        # 3. Sort by combined RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        hybrid_results = []
        for cid in sorted_cids:
            base_res = chunk_map[cid]
            hybrid_res = SearchResult(
                chunk_id=base_res.chunk_id,
                document_name=base_res.document_name,
                document_number=base_res.document_number,
                chapter=base_res.chapter,
                article=base_res.article,
                clause=base_res.clause,
                point=base_res.point,
                page_start=base_res.page_start,
                page_end=base_res.page_end,
                text=base_res.text,
                score=rrf_scores[cid],
                bm25_rank=bm25_ranks.get(cid),
                dense_rank=dense_ranks.get(cid),
                retrieval_method="hybrid_rrf"
            )
            hybrid_results.append(hybrid_res)

        return hybrid_results
