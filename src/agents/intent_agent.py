import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger("IntentAgent")

@dataclass
class IntentResult:
    domain: str                     # "labor_law", "social_insurance", "mixed", "out_of_scope"
    is_in_scope: bool
    raw_query: str
    normalized_query: str
    expanded_query: str
    extracted_keywords: List[str] = field(default_factory=list)
    matched_legal_concepts: List[str] = field(default_factory=list)
    confidence: float = 1.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "is_in_scope": self.is_in_scope,
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "expanded_query": self.expanded_query,
            "extracted_keywords": self.extracted_keywords,
            "matched_legal_concepts": self.matched_legal_concepts,
            "confidence": self.confidence,
            "explanation": self.explanation
        }


class IntentAgent:
    """
    Intent Agent:
    - Classifies legal domain: Labor Law, Social Insurance, Mixed, or Out-of-Scope.
    - Normalizes user questions (unicode, punctuation, whitespace).
    - Expands legal synonyms and colloquial keywords for high-precision retrieval.
    """

    # Keyword mappings for Vietnamese Labor Law (Bộ luật Lao động)
    LABOR_KEYWORDS = [
        "hợp đồng lao động", "thử việc", "nghỉ phép", "nghỉ hằng năm", "nghỉ hàng năm",
        "thời giờ làm việc", "thời giờ nghỉ ngơi", "làm thêm giờ", "làm đêm", "tăng ca",
        "tiền lương làm thêm", "ngừng việc", "tiền lương ngừng việc", "đơn phương chấm dứt",
        "chấm dứt hợp đồng", "sa thải", "kỷ luật lao động", "người sử dụng lao động",
        "người lao động", "trợ cấp thôi việc", "trợ cấp mất việc", "nội quy lao động",
        "hết hạn hợp đồng", "báo trước", "ngày nghỉ lễ", "nghỉ việc riêng"
    ]

    # Keyword mappings for Vietnamese Social Insurance (Luật BHXH)
    SOCIAL_INSURANCE_KEYWORDS = [
        "bảo hiểm xã hội", "bhxh", "chế độ ốm đau", "trợ cấp ốm đau", "ốm đau",
        "chế độ thai sản", "thai sản", "nghỉ thai sản", "sinh con", "nghỉ đẻ",
        "dưỡng sức", "phục hồi sức khỏe", "tai nạn lao động", "bệnh nghề nghiệp",
        "chế độ hưu trí", "lương hưu", "hưu trí", "tuổi nghỉ hưu", "tử tuất", "tiền tuất",
        "mai táng phí", "bhxh một lần", "rút bhxh", "sổ bảo hiểm xã hội",
        "đóng bảo hiểm xã hội", "mức hưởng bảo hiểm", "quỹ bảo hiểm"
    ]

    # Explicit Out-of-Scope Indicators (Criminal, Civil, Traffic, Chit-chat, etc.)
    OUT_OF_SCOPE_KEYWORDS = [
        "thời tiết", "nấu ăn", "công thức", "thơ ca", "viết code", "lập trình",
        "luật hình sự", "tội phạm", "án mạng", "buôn ma túy", "tù giam",
        "luật giao thông", "nồng độ cồn", "vượt đèn đỏ", "bằng lái xe",
        "luật đất đai", "sổ đỏ", "thừa kế", "ly hôn", "phân chia tài sản",
        "chứng khoán", "tiền ảo", "bitcoin", "bạn tên là gì", "bạn là ai"
    ]

    # Synonym Expansion Dictionary: maps colloquial/user terms to precise legal terminology
    SYNONYM_EXPANSION_MAP = {
        "nghỉ đẻ": ["chế độ thai sản", "sinh con", "nghỉ thai sản lao động nữ"],
        "đẻ": ["sinh con", "thai sản"],
        "nghỉ thai sản": ["thời gian hưởng chế độ thai sản", "trợ cấp thai sản"],
        "tăng ca": ["làm thêm giờ", "tiền lương làm thêm giờ"],
        "nghỉ phép": ["nghỉ hằng năm", "ngày nghỉ phép hằng năm"],
        "nghỉ hàng năm": ["nghỉ hằng năm"],
        "đuổi việc": ["đơn phương chấm dứt hợp đồng lao động", "kỷ luật sa thải"],
        "bị sa thải": ["xử lý kỷ luật lao động sa thải"],
        "tiền thôi việc": ["trợ cấp thôi việc", "trợ cấp mất việc làm"],
        "tiền ốm": ["mức hưởng trợ cấp ốm đau", "chế độ ốm đau"],
        "ốm đau": ["trợ cấp ốm đau", "mức hưởng chế độ ốm đau"],
        "lương hưu": ["chế độ hưu trí", "điều kiện hưởng lương hưu", "tuổi nghỉ hưu"],
        "về hưu": ["chế độ hưu trí", "tuổi nghỉ hưu"],
        "ngừng việc": ["tiền lương ngừng việc do lỗi"],
        "thử việc": ["thời gian thử việc", "hợp đồng thử việc"]
    }

    def __init__(self):
        logger.info("Khởi tạo IntentAgent thành công")

    def normalize_query(self, query: str) -> str:
        """Cleans and normalizes query text."""
        q = query.strip()
        q = re.sub(r"\s+", " ", q)
        return q

    def expand_query(self, query: str) -> Tuple[str, List[str], List[str]]:
        """
        Expands query with official legal synonyms.
        Returns: (expanded_query, added_terms, matched_concepts)
        """
        q_lower = query.lower()
        added_terms = []
        matched_concepts = []

        for phrase, legal_terms in self.SYNONYM_EXPANSION_MAP.items():
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, q_lower):
                matched_concepts.append(phrase)
                for term in legal_terms:
                    if term.lower() not in q_lower and term not in added_terms:
                        added_terms.append(term)

        # Build expanded query string
        if added_terms:
            expanded_query = f"{query} {' '.join(added_terms)}"
        else:
            expanded_query = query

        return expanded_query, added_terms, matched_concepts

    def classify_intent(self, raw_query: str) -> IntentResult:
        """
        Performs full intent classification, query normalization, and legal expansion.
        """
        normalized_q = self.normalize_query(raw_query)
        q_lower = normalized_q.lower()

        # 1. Check Out-of-scope triggers
        for oos_kw in self.OUT_OF_SCOPE_KEYWORDS:
            if oos_kw in q_lower:
                logger.info(f"Phát hiện câu hỏi ngoài phạm vi: '{oos_kw}' trong '{normalized_q}'")
                return IntentResult(
                    domain="out_of_scope",
                    is_in_scope=False,
                    raw_query=raw_query,
                    normalized_query=normalized_q,
                    expanded_query=normalized_q,
                    extracted_keywords=[oos_kw],
                    confidence=0.95,
                    explanation=f"Câu hỏi có chứa chủ đề ngoài phạm vi tư vấn lao động/BHXH: '{oos_kw}'"
                )

        # 2. Count keyword hits for labor vs social insurance
        labor_hits = [kw for kw in self.LABOR_KEYWORDS if kw in q_lower]
        social_hits = [kw for kw in self.SOCIAL_INSURANCE_KEYWORDS if kw in q_lower]

        # 3. Check for specific question patterns
        # E.g. "nghỉ đẻ công ty có phải trả lương hay bảo hiểm xã hội chi trả" -> Mixed
        is_mixed = False
        if labor_hits and social_hits:
            # If only generic term 'người lao động' matched in labor, but specific regime in social, prioritize social_insurance
            if labor_hits == ["người lao động"] and any(k in q_lower for k in ["chế độ ốm đau", "ốm đau", "thai sản", "nghỉ thai sản", "chế độ thai sản", "hưu trí", "lương hưu", "tử tuất"]):
                is_mixed = False
            else:
                is_mixed = True
        elif ("công ty" in q_lower or "người sử dụng lao động" in q_lower or "trả lương" in q_lower) and \
             ("bảo hiểm xã hội" in q_lower or "bhxh" in q_lower or "nghỉ đẻ" in q_lower or "thai sản" in q_lower):
            is_mixed = True

        # 4. Determine domain
        if is_mixed:
            domain = "mixed"
            confidence = 0.95
            explanation = "Câu hỏi liên quan đến cả Bộ luật Lao động và Luật Bảo hiểm xã hội"
        elif social_hits and not labor_hits:
            domain = "social_insurance"
            confidence = 0.95
            explanation = f"Câu hỏi thuộc lĩnh vực Luật Bảo hiểm xã hội (Từ khóa: {', '.join(social_hits[:3])})"
        elif labor_hits and not social_hits:
            domain = "labor_law"
            confidence = 0.95
            explanation = f"Câu hỏi thuộc lĩnh vực Bộ luật Lao động (Từ khóa: {', '.join(labor_hits[:3])})"
        else:
            # Fallback heuristic: check if contains words related to legal work
            general_work_kw = ["lương", "việc", "hợp đồng", "nghỉ", "chế độ", "công ty", "bảo hiểm", "bồi thường"]
            matched_gen = [w for w in general_work_kw if w in q_lower]
            if matched_gen:
                domain = "labor_law"
                confidence = 0.70
                explanation = "Nhận diện thuộc lĩnh vực lao động chung dựa trên từ khóa ngữ cảnh"
            else:
                domain = "out_of_scope"
                confidence = 0.85
                explanation = "Không phát hiện từ khóa liên quan đến quan hệ lao động hoặc bảo hiểm xã hội"
                return IntentResult(
                    domain=domain,
                    is_in_scope=False,
                    raw_query=raw_query,
                    normalized_query=normalized_q,
                    expanded_query=normalized_q,
                    extracted_keywords=[],
                    confidence=confidence,
                    explanation=explanation
                )

        # 5. Expand synonyms
        expanded_q, added_terms, matched_concepts = self.expand_query(normalized_q)

        all_keywords = list(set(labor_hits + social_hits + added_terms))
        logger.info(f"Intent: domain={domain}, matched_concepts={matched_concepts}, added_terms={added_terms}")

        return IntentResult(
            domain=domain,
            is_in_scope=True,
            raw_query=raw_query,
            normalized_query=normalized_q,
            expanded_query=expanded_q,
            extracted_keywords=all_keywords,
            matched_legal_concepts=matched_concepts,
            confidence=confidence,
            explanation=explanation
        )
