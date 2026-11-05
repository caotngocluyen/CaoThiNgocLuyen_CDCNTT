import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from config import DOCUMENTS_CONFIG
from src.agents.intent_agent import IntentResult
from src.agents.retrieval_agent import RetrievalContext
from src.agents.legal_analysis_agent import LegalAnalysisResult
from src.agents.validation_agent import ValidationResult
from src.utils.logger import get_logger

logger = get_logger("ResponseAgent")

@dataclass
class FinalResponse:
    conclusion: str
    legal_basis: List[Dict[str, Any]]
    explanation: str
    important_notes: List[str]
    formatted_markdown: str
    confidence_level: str               # "CAO", "TRUNG_BÌNH", "THẤP"
    domain_tag: str
    is_answerable: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "legal_basis": self.legal_basis,
            "explanation": self.explanation,
            "important_notes": self.important_notes,
            "formatted_markdown": self.formatted_markdown,
            "confidence_level": self.confidence_level,
            "domain_tag": self.domain_tag,
            "is_answerable": self.is_answerable
        }


class ResponseAgent:
    """
    Response Agent:
    - Formats clear, professional Vietnamese legal consultation responses.
    - Enforces standard 4-section structure:
      1. KẾT LUẬN (Direct conclusion)
      2. CĂN CỨ PHÁP LÝ (Detailed official citation with doc, article, clause, page, dates)
      3. GIẢI THÍCH CHI TIẾT (Comprehensive breakdown of rights, conditions, rates, deadlines)
      4. LƯU Ý QUAN TRỌNG (Legal validity status, exceptions, practical advice)
    - Rejects out-of-scope inquiries and handles insufficient-data states gracefully.
    """

    def __init__(self):
        logger.info("Khởi tạo ResponseAgent thành công")

    def format_response(
        self,
        intent: IntentResult,
        retrieval_ctx: Optional[RetrievalContext],
        analysis: Optional[LegalAnalysisResult],
        validation: Optional[ValidationResult]
    ) -> FinalResponse:
        """
        Synthesizes information from all previous agents into a finalized client-ready response.
        """
        # Case 1: Out of Scope
        if not intent.is_in_scope:
            return self._handle_out_of_scope(intent)

        # Case 2: Insufficient retrieval or analysis
        if not analysis or not analysis.is_sufficient or (retrieval_ctx and len(retrieval_ctx.all_chunks) == 0):
            return self._handle_insufficient_evidence(intent)

        # Case 3: Fully grounded response
        return self._build_grounded_response(intent, retrieval_ctx, analysis, validation)

    def _handle_out_of_scope(self, intent: IntentResult) -> FinalResponse:
        conclusion = "Câu hỏi nằm ngoài phạm vi tư vấn của hệ thống."
        explanation = (
            "Hệ thống Agentic Legal Chatbot hiện tại chuyên sâu tư vấn về **Bộ luật Lao động** "
            "(Văn bản hợp nhất số 18/VBHN-VPQH) và **Luật Bảo hiểm xã hội** (Luật số 41/2024/QH15) của Việt Nam.\n\n"
            f"Vấn đề bạn quan tâm ({intent.explanation}) thuộc lĩnh vực khác. "
            "Để được hỗ trợ chính xác, vui lòng đặt các câu hỏi liên quan đến hợp đồng lao động, "
            "tiền lương, thời giờ làm việc, nghỉ phép, chế độ thai sản, ốm đau, hưu trí hoặc quyền lợi bảo hiểm xã hội."
        )
        md = (
            f"### THÔNG BÁO PHẠM VI TƯ VẤN\n\n"
            f"**{conclusion}**\n\n"
            f"{explanation}\n"
        )
        return FinalResponse(
            conclusion=conclusion,
            legal_basis=[],
            explanation=explanation,
            important_notes=["Vui lòng đặt câu hỏi thuộc lĩnh vực Lao động hoặc Bảo hiểm xã hội."],
            formatted_markdown=md,
            confidence_level="CAO",
            domain_tag="out_of_scope",
            is_answerable=False
        )

    def _handle_insufficient_evidence(self, intent: IntentResult) -> FinalResponse:
        conclusion = "Chưa đủ căn cứ pháp lý trong cơ sở dữ liệu hiện tại để đưa ra câu trả lời khẳng định."
        explanation = (
            "Hệ thống đã tra cứu các quy định trong Bộ luật Lao động và Luật Bảo hiểm xã hội nhưng "
            "chưa tìm thấy điều khoản quy định trực tiếp hoặc cụ thể cho tình huống bạn nêu.\n\n"
            "Để tránh cung cấp thông tin không có căn cứ pháp luật xác thực, hệ thống khuyến nghị bạn "
            "cung cấp thêm chi tiết về tình huống hoặc tham vấn trực tiếp cơ quan BHXH / Phòng Lao động - Thương binh & Xã hội."
        )
        md = (
            f"### CHƯA ĐỦ CĂN CỨ PHÁP LÝ\n\n"
            f"**1. KẾT LUẬN:**\n{conclusion}\n\n"
            f"**2. GIẢI THÍCH:**\n{explanation}\n"
        )
        return FinalResponse(
            conclusion=conclusion,
            legal_basis=[],
            explanation=explanation,
            important_notes=["Hệ thống tuân thủ nguyên tắc không suy đoán khi thiếu căn cứ luật."],
            formatted_markdown=md,
            confidence_level="TRUNG_BÌNH",
            domain_tag=intent.domain,
            is_answerable=False
        )

    def _build_grounded_response(
        self,
        intent: IntentResult,
        retrieval_ctx: RetrievalContext,
        analysis: LegalAnalysisResult,
        validation: Optional[ValidationResult]
    ) -> FinalResponse:
        conclusion = analysis.conclusion

        # 1. Compile Legal Basis
        legal_basis = []
        basis_lines = []

        citations = validation.verified_citations if (validation and validation.verified_citations) else [c.to_dict() for c in analysis.legal_citations]

        for cit in citations:
            doc_name = cit.get("document_name", "")
            doc_num = cit.get("document_number", "")
            art = cit.get("article", "")
            clause = cit.get("clause", "")
            page = cit.get("page_start", "")

            # Look up doc config for status and effective date
            doc_info = None
            for key, conf in DOCUMENTS_CONFIG.items():
                if conf["document_number"] == doc_num:
                    doc_info = conf
                    break

            if doc_info:
                if doc_num == "18/VBHN-VPQH":
                    date_str = f" (Xác thực VBHN: {doc_info.get('consolidation_date', '12/02/2026')}; Luật gốc 45/2019/QH14 hiệu lực từ {doc_info.get('effective_date', '01/01/2021')})"
                elif doc_num == "41/2024/QH15":
                    date_str = f" (Ban hành: {doc_info.get('promulgation_date', '29/06/2024')}, Hiệu lực từ: {doc_info.get('effective_date', '01/07/2025')})"
                else:
                    date_str = f" (Ban hành: {doc_info.get('promulgation_date')}, Trạng thái: {doc_info.get('status')})"
            else:
                date_str = ""

            page_str = f" - Trang {page}" if page else ""

            basis_item = {
                "document": f"{doc_name} (Số {doc_num}){date_str}",
                "article": art,
                "clause": clause,
                "page": page
            }
            legal_basis.append(basis_item)
            basis_lines.append(f"- **{doc_name} (Số {doc_num})**: {art}, {clause}{page_str}{date_str}")

        if not basis_lines:
            basis_lines.append("- Tham chiếu các quy định pháp luật lao động / BHXH hiện hành trong hệ thống.")

        # 2. Detailed Explanation
        explanation_parts = []
        if analysis.conditions:
            explanation_parts.append("**Điều kiện và mức áp dụng cụ thể:**")
            for cond in analysis.conditions:
                explanation_parts.append(f"+ {cond}")

        # Add excerpt from LLM raw response if structured
        raw = analysis.raw_llm_response
        if "ĐIỀU KIỆN" in raw or "CĂN CỨ" in raw:
            # Clean explanation text
            clean_exp = re.sub(r"^(?:KẾT LUẬN|CĂN CỨ PHÁP LÝ):.*?(?=(?:ĐIỀU KIỆN|LƯU Ý|$))", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
            if clean_exp and not explanation_parts:
                explanation_parts.append(clean_exp)
        elif not explanation_parts:
            explanation_parts.append(raw)

        explanation = "\n".join(explanation_parts)

        # 3. Important Notes & Exceptions
        notes = []
        if analysis.exceptions:
            for exc in analysis.exceptions:
                notes.append(f"Quy định ngoại lệ: {exc}")

        # Add document validity notices
        for cit in legal_basis:
            doc_str = cit.get("document", "")
            if "41/2024/QH15" in doc_str:
                notes.append("Lưu ý về hiệu lực: Luật Bảo hiểm xã hội số 41/2024/QH15 được Quốc hội khóa XV thông qua ngày 29/06/2024 và chính thức có hiệu lực thi hành từ ngày 01/07/2025.")
            if "18/VBHN-VPQH" in doc_str:
                notes.append("Lưu ý về hiệu lực: Áp dụng theo Văn bản hợp nhất số 18/VBHN-VPQH (Xác thực ngày 12/02/2026; Bộ luật Lao động gốc số 45/2019/QH14 có hiệu lực từ ngày 01/01/2021).")

        if validation and validation.warning_messages:
            for w in validation.warning_messages:
                notes.append(f"Cảnh báo kiểm định: {w}")

        # Remove duplicate notes
        notes = list(dict.fromkeys(notes))

        # 4. Generate Final Markdown Response
        md_lines = [
            "### KẾT QUẢ TƯ VẤN PHÁP LUẬT",
            "",
            "#### 1. KẾT LUẬN",
            conclusion,
            "",
            "#### 2. CĂN CỨ PHÁP LÝ",
            "\n".join(basis_lines),
            "",
            "#### 3. GIẢI THÍCH CHI TIẾT",
            explanation,
            "",
            "#### 4. LƯU Ý VÀ ÁP DỤNG THỰC TIỄN",
            "\n".join([f"- {n}" for n in notes]) if notes else "- Tuân thủ các trình tự, thủ tục hồ sơ theo quy định của pháp luật."
        ]

        formatted_markdown = "\n".join(md_lines)
        confidence = "CAO" if (validation and validation.is_valid and validation.validation_status == "PASSED") else "TRUNG_BÌNH"

        return FinalResponse(
            conclusion=conclusion,
            legal_basis=legal_basis,
            explanation=explanation,
            important_notes=notes,
            formatted_markdown=formatted_markdown,
            confidence_level=confidence,
            domain_tag=intent.domain,
            is_answerable=True
        )
