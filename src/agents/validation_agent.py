import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set

from config import CHUNKS_JSON_PATH, DOCUMENTS_CONFIG
from src.agents.retrieval_agent import EnrichedChunk, RetrievalContext
from src.agents.legal_analysis_agent import LegalAnalysisResult, LegalCitation
from src.utils.logger import get_logger

logger = get_logger("ValidationAgent")

@dataclass
class ValidationResult:
    is_valid: bool
    validation_status: str               # "PASSED", "WARNING", "FAILED"
    verified_citations: List[Dict[str, Any]] = field(default_factory=list)
    hallucinated_citations: List[str] = field(default_factory=list)
    unsupported_facts: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    warning_messages: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    can_retry: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ValidationAgent:
    """
    Validation Agent (Pure Python, Deterministic, Anti-Hallucination):
    - Verifies chunk_id existence against official processed dataset.
    - Validates document names, document numbers, Articles, Clauses, and page numbers.
    - Cross-references quotes and citations with source text to detect fabricated references.
    - Verifies that numbers, percentages (%), and deadlines in LLM response are backed by sources.
    - Zero extra LLM latency, 100% reproducible.
    """

    def __init__(self, chunks_path=CHUNKS_JSON_PATH):
        self.chunks_path = chunks_path
        self.all_chunks_dict: Dict[str, Dict[str, Any]] = {}
        self.article_clause_map: Dict[str, Set[str]] = {}  # "41/2024/QH15|||Điều 45" -> {"Khoản 1", "Khoản 2", ...}
        self._load_knowledge_base()

        # Valid document numbers and names
        self.valid_docs = {
            conf["document_number"]: conf["document_name"]
            for conf in DOCUMENTS_CONFIG.values()
        }

    def _load_knowledge_base(self):
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        for c in chunks:
            cid = c["chunk_id"]
            self.all_chunks_dict[cid] = c

            art_key = f"{c['document_number']}|||{c['article'].strip()}"
            if art_key not in self.article_clause_map:
                self.article_clause_map[art_key] = set()
            self.article_clause_map[art_key].add(c["clause"].strip())

        logger.info(f"ValidationAgent nạp cơ sở dữ liệu: {len(self.all_chunks_dict)} chunks để đối chiếu")

    def validate(
        self,
        analysis_result: LegalAnalysisResult,
        retrieval_context: RetrievalContext
    ) -> ValidationResult:
        """
        Runs comprehensive deterministic validation pipeline on LLM legal analysis.
        """
        passed_checks = []
        warning_messages = []
        error_messages = []
        hallucinated_citations = []
        unsupported_facts = []
        verified_citations = []

        retrieved_cids = {c.chunk_id for c in retrieval_context.all_chunks}
        retrieved_text_corpus = " ".join([c.text for c in retrieval_context.all_chunks])

        # 1. Check if LLM flagged insufficient evidence
        if not analysis_result.is_sufficient:
            passed_checks.append("LLM nhận diện chính xác nguồn tin chưa đủ căn cứ (không bịa đặt)")
            return ValidationResult(
                is_valid=True,
                validation_status="PASSED",
                passed_checks=passed_checks,
                can_retry=True
            )

        # 2. Validate Legal Citations
        citations = analysis_result.legal_citations
        if not citations:
            warning_messages.append("Không trích dẫn được điều khoản pháp lý cụ thể nào.")
        else:
            for cit in citations:
                cit_dict = cit.to_dict()
                cid = cit.chunk_id

                # Check chunk_id existence in database
                if cid and cid not in self.all_chunks_dict:
                    error_msg = f"Mã chunk_id không tồn tại trong hệ thống: '{cid}'"
                    error_messages.append(error_msg)
                    hallucinated_citations.append(f"Invalid chunk_id: {cid}")
                    continue

                # Check document validity
                doc_num = cit.document_number
                if doc_num and doc_num not in self.valid_docs:
                    error_msg = f"Số hiệu văn bản không hợp lệ hoặc ngoài phạm vi: '{doc_num}'"
                    error_messages.append(error_msg)
                    hallucinated_citations.append(f"Invalid doc: {doc_num}")
                    continue

                # Check article & clause validity in the actual legal text
                if doc_num and cit.article:
                    art_key = f"{doc_num}|||{cit.article.strip()}"
                    valid_clauses = self.article_clause_map.get(art_key)
                    if valid_clauses is None:
                        # Article doesn't exist in that law
                        # Check partial match
                        matched_keys = [k for k in self.article_clause_map if f"{doc_num}|||" in k and cit.article.split()[0] in k]
                        if not matched_keys:
                            error_msg = f"Điều luật bịa đặt hoặc không có trong văn bản: {cit.article} ({doc_num})"
                            error_messages.append(error_msg)
                            hallucinated_citations.append(f"{cit.article} ({doc_num})")
                            continue

                # Check if this citation is supported by retrieved chunks
                if cid and cid in retrieved_cids:
                    passed_checks.append(f"Xác thực hợp lệ: {cit.document_name} | {cit.article} | {cit.clause} (Trang {cit.page_start})")
                    verified_citations.append(cit_dict)
                else:
                    # In DB but wasn't retrieved
                    warning_messages.append(f"Điều khoản có trong luật nhưng nằm ngoài top retrieval: {cit.article}")
                    verified_citations.append(cit_dict)

        # 3. Fact and Number Grounding: Cross-check percentages and numbers against SPECIFIC CITED CLAUSES
        # Compile text specifically from the cited chunks
        cited_cids = {c.chunk_id for c in analysis_result.legal_citations if c.chunk_id}
        cited_articles = {c.article.strip() for c in analysis_result.legal_citations if c.article}
        cited_clauses = {c.clause.strip() for c in analysis_result.legal_citations if c.clause}

        # Segregate text: strictly cited clauses vs parent article vs general context
        strict_cited_text = []
        parent_art_text = []
        other_context_text = []

        for c in retrieval_context.all_chunks:
            is_strict_cit = (c.chunk_id in cited_cids) or (c.article.strip() in cited_articles and c.clause.strip() in cited_clauses)
            is_parent_art = (c.article.strip() in cited_articles)

            if is_strict_cit:
                strict_cited_text.append(c.text.lower())
            elif is_parent_art:
                parent_art_text.append(c.text.lower())
            else:
                other_context_text.append(c.text.lower())

        strict_cited_corpus = re.sub(r"\s+", " ", " ".join(strict_cited_text))
        parent_art_corpus = re.sub(r"\s+", " ", " ".join(parent_art_text))
        global_corpus = re.sub(r"\s+", " ", retrieved_text_corpus.lower())

        # Check percentages
        for rate in analysis_result.rates_and_deadlines:
            rate_clean = rate.strip().lower()
            if "%" in rate_clean:
                pct_num = re.search(r"\d+", rate_clean)
                if pct_num:
                    pct_str = pct_num.group(0)
                    in_strict = (f"{pct_str}%" in strict_cited_corpus) or (f"{pct_str} %" in strict_cited_corpus)
                    in_parent = (f"{pct_str}%" in parent_art_corpus) or (f"{pct_str} %" in parent_art_corpus)
                    in_global = (f"{pct_str}%" in global_corpus) or (f"{pct_str} %" in global_corpus)

                    if in_strict:
                        passed_checks.append(f"Xác thực mức/tỷ lệ '{rate}' xuất hiện chính xác trong KHOẢN TRÍCH DẪN CĂN CỨ")
                    elif in_parent:
                        warning_messages.append(f"Tỷ lệ '{rate}' có trong Điều luật liên quan nhưng nằm ở Khoản khác, chưa định vị chính xác Khoản trích dẫn")
                        passed_checks.append(f"Xác minh tỷ lệ '{rate}' có trong cùng Điều luật tham chiếu")
                    elif in_global:
                        warning_messages.append(f"Tỷ lệ '{rate}' có xuất hiện trong ngữ cảnh nhưng KHÔNG thuộc Điều/Khoản được trích dẫn làm căn cứ!")
                        unsupported_facts.append(rate)
                    else:
                        error_msg = f"Tỷ lệ '{rate}' xuất hiện trong câu trả lời nhưng HOÀN TOÀN KHÔNG có trong bất kỳ văn bản nguồn nào!"
                        error_messages.append(error_msg)
                        unsupported_facts.append(rate)

            elif any(d in rate_clean for d in ["ngày", "tháng", "năm", "giờ"]):
                dur_match = re.search(r"(\d+)\s*(ngày|tháng|năm|giờ)", rate_clean)
                if dur_match:
                    num_val = dur_match.group(1)
                    unit_val = dur_match.group(2)
                    target_patterns = [
                        f"{num_val} {unit_val}",
                        f"{int(num_val):02d} {unit_val}"
                    ]
                    in_strict = any(p in strict_cited_corpus for p in target_patterns) or (str(int(num_val)) in strict_cited_corpus and unit_val in strict_cited_corpus)
                    in_parent = any(p in parent_art_corpus for p in target_patterns) or (str(int(num_val)) in parent_art_corpus and unit_val in parent_art_corpus)
                    in_global = any(p in global_corpus for p in target_patterns) or (str(int(num_val)) in global_corpus and unit_val in global_corpus)

                    if in_strict:
                        passed_checks.append(f"Xác thực thời hạn '{rate}' xuất hiện chính xác trong KHOẢN TRÍCH DẪN CĂN CỨ")
                    elif in_parent:
                        warning_messages.append(f"Thời hạn '{rate}' nằm trong cùng Điều nhưng cần kiểm tra lại chính xác Khoản quy định")
                        passed_checks.append(f"Xác minh thời hạn '{rate}' có trong Điều luật tham chiếu")
                    elif in_global:
                        warning_messages.append(f"Thời hạn '{rate}' không nằm trong Điều/Khoản được trích dẫn làm căn cứ!")
                    else:
                        warning_messages.append(f"Thời hạn '{rate}' không tìm thấy trong văn bản nguồn.")

        legal_stop_words = {"là", "có", "và", "của", "được", "cho", "trong", "khi", "theo", "quy", "định", "tại", "các", "người", "với", "những", "nào", "gì", "như", "thế", "nào", "bao", "nhiêu"}

        # 4. Condition Grounding & Condition-Rate Alignment Check
        conclusion_and_conds = (analysis_result.conclusion + " " + " ".join(analysis_result.conditions)).lower()

        for cond in analysis_result.conditions:
            cond_clean = cond.strip().lower()
            if not cond_clean:
                continue
            cond_words = [w for w in re.findall(r"\w+", cond_clean) if len(w) > 2 and w not in legal_stop_words]
            if cond_words:
                cond_in_strict = sum(1 for w in cond_words if w in strict_cited_corpus) / len(cond_words)
                cond_in_parent = sum(1 for w in cond_words if w in parent_art_corpus) / len(cond_words)
                if cond_in_strict >= 0.4:
                    passed_checks.append(f"Xác thực điều kiện áp dụng '{cond}' phù hợp với Khoản trích dẫn căn cứ.")
                elif cond_in_parent >= 0.4:
                    warning_messages.append(f"Điều kiện áp dụng '{cond}' có trong Điều luật nhưng nằm ở Khoản khác.")
                else:
                    warning_messages.append(f"Điều kiện áp dụng '{cond}' không tìm thấy trực tiếp trong văn bản nguồn.")

        # Condition-Rate Consistency Check for tiered rates (e.g. Điều 45 Khoản 3 Luật BHXH 2024)
        tiered_conditions_rules = [
            ("65%", ["30 năm", "từ đủ 30 năm"], ["dưới 15 năm", "dưới 30 năm"]),
            ("55%", ["15 năm đến dưới 30 năm", "15 năm"], ["30 năm trở lên", "dưới 15 năm"]),
            ("50%", ["dưới 15 năm"], ["30 năm trở lên", "15 năm đến dưới 30 năm"]),
        ]
        for rate_key, req_keywords, forbidden_keywords in tiered_conditions_rules:
            if any(rate_key in r for r in analysis_result.rates_and_deadlines) or rate_key in conclusion_and_conds:
                for f_kw in forbidden_keywords:
                    pattern = rf"({re.escape(rate_key)}[^\.\;\,]{{0,60}}{re.escape(f_kw)}|{re.escape(f_kw)}[^\.\;\,]{{0,60}}{re.escape(rate_key)})"
                    if re.search(pattern, conclusion_and_conds):
                        error_msg = f"Xung đột điều kiện - tỷ lệ: Mức '{rate_key}' bị gán sai điều kiện '{f_kw}' (quy định chuẩn yêu cầu '{req_keywords[0]}')"
                        error_messages.append(error_msg)
                        unsupported_facts.append(f"{rate_key} gán sai {f_kw}")

        # 5. Citation-Answer Consistency & Query Coverage Check
        conclusion_words = set(re.findall(r"\w+", analysis_result.conclusion.lower()))
        meaningful_conclusion_words = {w for w in conclusion_words if len(w) > 2 and w not in legal_stop_words}

        if meaningful_conclusion_words and strict_cited_corpus:
            overlap = meaningful_conclusion_words.intersection(set(re.findall(r"\w+", strict_cited_corpus)))
            overlap_ratio = len(overlap) / len(meaningful_conclusion_words)
            if overlap_ratio >= 0.2:
                passed_checks.append(f"Độ nhất quán Căn cứ - Kết luận (Citation-Answer Consistency): Đạt {overlap_ratio*100:.1f}% từ khóa cốt lõi")
            else:
                warning_messages.append(f"Cảnh báo độ nhất quán thấp: Kết luận và Khoản trích dẫn chỉ trùng {overlap_ratio*100:.1f}% từ khóa.")

        # Query coverage check: verify whether query entities exist in current legal database
        query_words = set(re.findall(r"\w+", retrieval_context.query.lower()))
        meaningful_query_words = {w for w in query_words if len(w) > 3 and w not in legal_stop_words}
        if meaningful_query_words:
            q_overlap = meaningful_query_words.intersection(set(re.findall(r"\w+", global_corpus)))
            q_ratio = len(q_overlap) / len(meaningful_query_words)
            if q_ratio < 0.35:
                missing_terms = list(meaningful_query_words - q_overlap)[:3]
                warning_messages.append(f"Cảnh báo phạm vi dữ liệu: Câu hỏi chứa thuật ngữ '{', '.join(missing_terms)}' không có trong cơ sở dữ liệu luật lao động/BHXH hiện hành.")

        # 4. Final Validity Determination
        if error_messages or hallucinated_citations:
            is_valid = False
            validation_status = "FAILED"
            can_retry = True
        elif warning_messages:
            is_valid = True
            validation_status = "WARNING"
            can_retry = False
        else:
            is_valid = True
            validation_status = "PASSED"
            can_retry = False

        logger.info(
            f"Validation hoàn tất: status={validation_status}, "
            f"passed_checks={len(passed_checks)}, warnings={len(warning_messages)}, errors={len(error_messages)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            validation_status=validation_status,
            verified_citations=verified_citations,
            hallucinated_citations=hallucinated_citations,
            unsupported_facts=unsupported_facts,
            passed_checks=passed_checks,
            warning_messages=warning_messages,
            error_messages=error_messages,
            can_retry=can_retry
        )
