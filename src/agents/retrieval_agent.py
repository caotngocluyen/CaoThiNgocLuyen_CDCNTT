import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from config import (
    BM25_INDEX_PATH,
    CHUNKS_JSON_PATH,
    DOCUMENTS_CONFIG,
    RETRIEVAL_TOP_K,
    RETRIEVAL_CANDIDATE_POOL,
    PARENT_CHILD_EXPAND,
    MAX_PARENT_CHILD_SIBLINGS,
    RRF_K,
    RRF_WEIGHT_BM25,
    RRF_WEIGHT_DENSE
)
from src.retrieval.hybrid_search import BM25Searcher, DenseVectorSearcher, HybridLegalRetriever, SearchResult
from src.retrieval.embedding import LegalEmbeddingModel
from src.utils.logger import get_logger

logger = get_logger("RetrievalAgent")

@dataclass
class EnrichedChunk:
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
    retrieval_rank: int
    retrieval_method: str
    bm25_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    is_parent_child_expanded: bool = False
    parent_article: str = ""
    promulgation_date: str = ""
    effective_status: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalContext:
    query: str
    expanded_query: str
    primary_chunks: List[EnrichedChunk]
    expanded_chunks: List[EnrichedChunk]
    all_chunks: List[EnrichedChunk]
    unique_articles: List[str]
    total_retrieved: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "expanded_query": self.expanded_query,
            "primary_chunks": [c.to_dict() for c in self.primary_chunks],
            "expanded_chunks": [c.to_dict() for c in self.expanded_chunks],
            "all_chunks": [c.to_dict() for c in self.all_chunks],
            "unique_articles": self.unique_articles,
            "total_retrieved": self.total_retrieved
        }


class RetrievalAgent:
    """
    Retrieval Agent:
    - Coordinates BM25 Lexical + ChromaDB Semantic search via HybridLegalRetriever (RRF).
    - Performs Parent-Child Context Expansion at Article level to ensure complete clause coverage.
    - Enriches chunks with official metadata (dates, legal validity, source pages).
    - Guarantees exact clause availability for tricky questions like Q14 (Điều 45 Khoản 2).
    """

    def __init__(
        self,
        hybrid_retriever: Optional[HybridLegalRetriever] = None,
        chunks_path=CHUNKS_JSON_PATH,
        expand_parent_child: bool = PARENT_CHILD_EXPAND,
        max_siblings: int = MAX_PARENT_CHILD_SIBLINGS
    ):
        self.expand_parent_child = expand_parent_child
        self.max_siblings = max_siblings
        self.chunks_path = chunks_path

        # 1. Initialize Hybrid Retriever if not passed
        if hybrid_retriever is not None:
            self.retriever = hybrid_retriever
        else:
            logger.info("Đang khởi tạo BM25Searcher và DenseVectorSearcher...")
            bm25 = BM25Searcher(BM25_INDEX_PATH)
            bm25.load_index()
            emb = LegalEmbeddingModel()
            dense = DenseVectorSearcher(emb)
            self.retriever = HybridLegalRetriever(
                bm25_searcher=bm25,
                dense_searcher=dense,
                k=RRF_K,
                w_bm25=RRF_WEIGHT_BM25,
                w_dense=RRF_WEIGHT_DENSE
            )

        # 2. Build Article-to-Chunks index for fast Parent-Child expansion
        self.article_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.chunk_lookup: Dict[str, Dict[str, Any]] = {}
        self._load_chunks_index()

        # 3. Document metadata map
        self.doc_metadata: Dict[str, Dict[str, str]] = {}
        for key, conf in DOCUMENTS_CONFIG.items():
            doc_num = conf["document_number"]
            self.doc_metadata[doc_num] = {
                "promulgation_date": conf.get("promulgation_date", ""),
                "status": conf.get("status", "")
            }

        logger.info(f"RetrievalAgent sẵn sàng: Indexed {len(self.chunk_lookup)} chunks across {len(self.article_index)} articles")

    def _load_chunks_index(self):
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            all_chunks = json.load(f)

        for c in all_chunks:
            cid = c["chunk_id"]
            self.chunk_lookup[cid] = c
            # Key by (document_number, article)
            art_key = f"{c['document_number']}|||{c['article']}"
            self.article_index[art_key].append(c)

    def retrieve(
        self,
        query: str,
        expanded_query: Optional[str] = None,
        top_k: int = RETRIEVAL_TOP_K,
        candidate_pool: int = RETRIEVAL_CANDIDATE_POOL,
        force_expand: Optional[bool] = None
    ) -> RetrievalContext:
        """
        Executes hybrid search with optional Parent-Child context expansion.
        """
        search_query = expanded_query if expanded_query else query
        should_expand = force_expand if force_expand is not None else self.expand_parent_child

        # 1. Execute Hybrid Search (BM25 + Dense RRF)
        raw_results: List[SearchResult] = self.retriever.search(
            query=search_query,
            top_k=top_k,
            candidate_pool=candidate_pool
        )

        primary_chunks: List[EnrichedChunk] = []
        retrieved_cids: Set[str] = set()

        for rank, r in enumerate(raw_results, 1):
            retrieved_cids.add(r.chunk_id)
            meta = self.doc_metadata.get(r.document_number, {})
            primary_chunks.append(EnrichedChunk(
                chunk_id=r.chunk_id,
                document_name=r.document_name,
                document_number=r.document_number,
                chapter=r.chapter,
                article=r.article,
                clause=r.clause,
                point=r.point,
                page_start=r.page_start,
                page_end=r.page_end,
                text=r.text,
                score=r.score,
                retrieval_rank=rank,
                retrieval_method=r.retrieval_method,
                bm25_rank=r.bm25_rank,
                dense_rank=r.dense_rank,
                is_parent_child_expanded=False,
                parent_article=r.article,
                promulgation_date=meta.get("promulgation_date", ""),
                effective_status=meta.get("status", "")
            ))

        # 2. Parent-Child Expansion: Retrieve sibling clauses within the same Article
        expanded_chunks: List[EnrichedChunk] = []
        if should_expand:
            processed_articles: Set[str] = set()
            for r in primary_chunks:
                art_key = f"{r.document_number}|||{r.article}"
                if art_key in processed_articles:
                    continue
                processed_articles.add(art_key)

                siblings = self.article_index.get(art_key, [])
                added_siblings = 0
                for sib in siblings:
                    sib_id = sib["chunk_id"]
                    if sib_id in retrieved_cids:
                        continue
                    if added_siblings >= self.max_siblings:
                        break

                    meta = self.doc_metadata.get(sib["document_number"], {})
                    enriched_sib = EnrichedChunk(
                        chunk_id=sib_id,
                        document_name=sib["document_name"],
                        document_number=sib["document_number"],
                        chapter=sib["chapter"],
                        article=sib["article"],
                        clause=sib["clause"],
                        point=sib.get("point"),
                        page_start=sib["page_start"],
                        page_end=sib["page_end"],
                        text=sib["text"],
                        score=r.score * 0.95,  # Slightly discounted score for sibling
                        retrieval_rank=99,
                        retrieval_method="parent_child_expansion",
                        bm25_rank=None,
                        dense_rank=None,
                        is_parent_child_expanded=True,
                        parent_article=r.article,
                        promulgation_date=meta.get("promulgation_date", ""),
                        effective_status=meta.get("status", "")
                    )
                    expanded_chunks.append(enriched_sib)
                    retrieved_cids.add(sib_id)
                    added_siblings += 1

        # Combine all chunks
        all_chunks = primary_chunks + expanded_chunks
        unique_articles = list(dict.fromkeys([c.article for c in all_chunks]))

        logger.info(
            f"Retrieval hoàn thành: {len(primary_chunks)} primary chunks, "
            f"{len(expanded_chunks)} expanded chunks across {len(unique_articles)} articles."
        )

        return RetrievalContext(
            query=query,
            expanded_query=search_query,
            primary_chunks=primary_chunks,
            expanded_chunks=expanded_chunks,
            all_chunks=all_chunks,
            unique_articles=unique_articles,
            total_retrieved=len(all_chunks)
        )
