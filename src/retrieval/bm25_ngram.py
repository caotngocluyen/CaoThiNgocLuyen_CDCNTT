import re
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Okapi
from config import BASE_DIR, PROCESSED_DATA_DIR, TOP_K_DEFAULT
from src.retrieval.hybrid_search import SearchResult
from src.utils.logger import get_logger

logger = get_logger("BM25Ngram")

BM25_NGRAM_INDEX_PATH = PROCESSED_DATA_DIR / "bm25_index_ngram.pkl"

# Regex patterns for repairing intra-syllable spaces introduced by PDF text extraction
# E.g. 'ngh ỉ' -> 'nghỉ', 'b ảo' -> 'bảo', 'c ủa' -> 'của', 's ản' -> 'sản', 'đ ộng' -> 'động'
P_SYLLABLE_ONSET_NUCLEUS = re.compile(
    r'\b(ngh|ng|th|ch|ph|kh|nh|tr|gi|qu|[bcdđghklmnpqrstvx])\s+([aăâeêioôơuưyàằầèềìồờùừỳáắấéếíốớúứýảẳẩẻểỉổởủửỷãẵẫẽễĩỗỡũữỹạặậẹệịộợụựỵ]\w*)\b',
    re.IGNORECASE
)
P_SYLLABLE_SPECIAL = re.compile(
    r'\b(ti|hư|th|ngư|đi|kho)\s+(ền|ởng|ời|ời|ều|ản)\b',
    re.IGNORECASE
)

# Comprehensive Legal Compounds dictionary for Vietnamese Labor & Social Insurance Law
LEGAL_COMPOUNDS = [
    # Hợp đồng lao động
    "hợp đồng lao động không xác định thời hạn",
    "hợp đồng lao động xác định thời hạn",
    "hợp đồng lao động",
    "các loại hợp đồng lao động",
    "loại hợp đồng lao động",
    "loại hợp đồng",
    "không xác định thời hạn",
    "xác định thời hạn",
    # Chấm dứt & Đơn phương
    "đơn phương chấm dứt hợp đồng lao động",
    "đơn phương chấm dứt",
    "chấm dứt hợp đồng lao động",
    "chấm dứt hợp đồng",
    "không được thực hiện quyền đơn phương",
    "không cần báo trước",
    "thời hạn báo trước",
    "báo trước",
    # Thử việc
    "thời gian thử việc",
    "hợp đồng thử việc",
    "trình độ cao đẳng trở lên",
    "trình độ cao đẳng",
    # Thời giờ làm việc, nghỉ ngơi
    "thời giờ làm việc bình thường",
    "thời giờ làm việc",
    "làm thêm giờ",
    "tiền lương làm thêm giờ",
    "ngày nghỉ hằng tuần",
    "ngày nghỉ hàng tuần",
    "nghỉ hằng năm",
    "nghỉ phép hàng năm",
    "nghỉ phép hằng năm",
    "ngừng việc do lỗi",
    "ngừng việc",
    # Nghĩa vụ khi chấm dứt
    "trách nhiệm của người sử dụng lao động",
    "trách nhiệm khi chấm dứt hợp đồng",
    "thanh toán các khoản",
    # Bảo hiểm xã hội
    "bảo hiểm xã hội bắt buộc",
    "tham gia bảo hiểm xã hội bắt buộc",
    "bảo hiểm xã hội",
    "đối tượng tham gia bảo hiểm xã hội",
    "đối tượng tham gia",
    "tiền lương làm căn cứ đóng",
    "tiền lương đóng bảo hiểm xã hội",
    # Ốm đau
    "điều kiện hưởng chế độ ốm đau",
    "chế độ ốm đau",
    "mức hưởng chế độ ốm đau",
    "mức hưởng trợ cấp ốm đau",
    "trợ cấp ốm đau",
    # Thai sản
    "điều kiện hưởng chế độ thai sản",
    "thời gian nghỉ việc hưởng chế độ thai sản",
    "thời gian nghỉ việc hưởng chế độ",
    "chế độ thai sản",
    "nghỉ thai sản",
    "lao động nữ sinh con",
    "lao động nữ",
    "sinh con",
    "nghỉ đẻ",
    # Hưu trí
    "điều kiện hưởng lương hưu",
    "tuổi nghỉ hưu",
    "hưởng lương hưu",
    "lương hưu",
    # Thôi việc & Thất nghiệp
    "trợ cấp thôi việc",
    "trợ cấp mất việc làm",
    "trợ cấp thất nghiệp",
    "bảo hiểm thất nghiệp",
    # Chủ thể & Thuật ngữ chung
    "người sử dụng lao động",
    "người lao động",
    "tai nạn lao động",
    "bệnh nghề nghiệp",
    "điều kiện hưởng",
    "mức hưởng",
    "tiền lương thực trả",
    "tiền lương theo hợp đồng lao động"
]

# Legal bigram seed words to restrict bigram generation to legal contexts
LEGAL_BIGRAM_SEEDS = {
    "hợp", "đồng", "lao", "động", "thử", "việc", "báo", "trước", "chấm", "dứt",
    "đơn", "phương", "thời", "giờ", "làm", "thêm", "nghỉ", "hằng", "năm",
    "tuần", "tiền", "lương", "ngừng", "bảo", "hiểm", "xã", "hội", "bắt", "buộc",
    "thai", "sản", "ốm", "đau", "hưu", "trí", "sinh", "con", "trợ", "cấp",
    "thất", "nghiệp", "thôi", "điều", "kiện", "mức", "hưởng", "đối", "tượng",
    "quyền", "nghĩa", "vụ", "trách", "nhiệm", "tai", "nạn", "bệnh", "nghề"
}


def normalize_legal_text(text: str) -> str:
    """
    Normalizes legal text by repairing broken syllables from PDF extraction
    and harmonizing frequent Vietnamese spelling variations.
    """
    text = text.lower()

    # Iterative repair for broken intra-syllable spaces
    prev = ""
    while prev != text:
        prev = text
        text = P_SYLLABLE_ONSET_NUCLEUS.sub(r"\1\2", text)
    text = P_SYLLABLE_SPECIAL.sub(r"\1\2", text)

    # Harmonize common legal spelling variations
    text = text.replace("nghỉ hàng năm", "nghỉ hằng năm")
    text = text.replace("ngày nghỉ hàng tuần", "ngày nghỉ hằng tuần")
    return text


def tokenize_vietnamese_legal_v2(text: str) -> List[str]:
    """
    Enhanced Vietnamese legal tokenizer (Phase 4.1):
    1. Syllable repair and legal normalization.
    2. Multi-word Legal Compound Dictionary extraction.
    3. Syllable unigrams (preserving numbers, slashes, roman numerals).
    4. Selective domain bigrams containing legal keywords.
    """
    norm_text = normalize_legal_text(text)

    # 1. Extract legal compound tokens
    compound_tokens: List[str] = []
    for comp in LEGAL_COMPOUNDS:
        if comp in norm_text:
            compound_tokens.append(comp.replace(" ", "_"))

    # 2. Extract base unigrams
    raw_tokens = re.findall(r"[\w\d/_\-]+", norm_text)
    unigrams = [t for t in raw_tokens if len(t) > 1 or t.isdigit()]

    # 3. Selective domain bigrams
    bigrams: List[str] = []
    for i in range(len(unigrams) - 1):
        w1, w2 = unigrams[i], unigrams[i + 1]
        if w1 in LEGAL_BIGRAM_SEEDS or w2 in LEGAL_BIGRAM_SEEDS:
            bigrams.append(f"{w1}_{w2}")

    return unigrams + compound_tokens + bigrams


class BM25NgramSearcher:
    """
    Enhanced BM25 Searcher using Legal Compound Dictionary and selective Word N-grams.
    Maintains 100% independence from the baseline bm25_index.pkl.
    """
    def __init__(self, index_path=BM25_NGRAM_INDEX_PATH):
        self.index_path = Path(index_path)
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[Dict[str, Any]] = []

    def build_index(self, chunks: List[Dict[str, Any]]):
        logger.info(f"Đang xây dựng BM25 N-gram index cho {len(chunks)} chunks...")
        self.chunks = chunks
        corpus = [tokenize_vietnamese_legal_v2(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
        logger.info(f"Đã lưu BM25 N-gram index vào {self.index_path}")

    def load_index(self) -> bool:
        if not self.index_path.exists():
            return False
        logger.info(f"Đang nạp BM25 N-gram index từ {self.index_path}...")
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.chunks = data["chunks"]
        logger.info(f"Nạp BM25 N-gram index thành công ({len(self.chunks)} chunks)")
        return True

    def search(self, query: str, top_k: int = TOP_K_DEFAULT) -> List[SearchResult]:
        if not self.bm25:
            raise ValueError("BM25 N-gram index chưa được khởi tạo!")

        tokenized_query = tokenize_vietnamese_legal_v2(query)
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
                retrieval_method="bm25_ngram"
            ))
        return results
