import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

from config import DOCUMENTS_CONFIG
from src.agents.retrieval_agent import EnrichedChunk

@dataclass
class ExtractedFactProfile:
    subjects: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    numbers_and_durations: List[str] = field(default_factory=list)
    legal_issues: List[str] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    temporal_clues: List[str] = field(default_factory=list)

class FactExtractor:
    """
    Deterministic rule-based fact and legal issue extractor.
    Runs in Python standard library (< 1 ms), providing structured grounding before LLM analysis.
    """

    SUBJECT_PATTERNS = [
        ("người lao động", r"\b(người lao động|nlđ|công nhân|nhân viên|lao động)\b"),
        ("người sử dụng lao động", r"\b(người sử dụng lao động|nsdlđ|công ty|doanh nghiệp|sếp|chủ)\b"),
        ("lao động nữ", r"\b(lao động nữ|nữ|phụ nữ|bầu|mang thai|thai sản|sinh con|nghỉ đẻ)\b"),
        ("cơ quan BHXH", r"\b(bảo hiểm xã hội|bhxh|quỹ bhxh|cơ quan bhxh)\b"),
    ]

    ACTION_PATTERNS = [
        ("thử việc", r"\b(thử việc|hợp đồng thử việc)\b"),
        ("đơn phương chấm dứt", r"\b(đơn phương|nghỉ việc|thôi việc|chấm dứt|bỏ việc|xin nghỉ)\b"),
        ("làm thêm giờ", r"\b(làm thêm|tăng ca|làm thêm giờ|ngoài giờ|chủ nhật|ngày nghỉ)\b"),
        ("nghỉ phép hàng năm", r"\b(nghỉ phép|phép năm|nghỉ hằng năm|ngày nghỉ phép)\b"),
        ("ngừng việc", r"\b(ngừng việc|tạm hoãn|nghỉ việc do lỗi)\b"),
        ("nghỉ ốm đau", r"\b(ốm đau|nghỉ ốm|bệnh tật|tai nạn|nằm viện)\b"),
        ("sinh con / thai sản", r"\b(sinh con|nghỉ đẻ|thai sản|mang thai|khám thai)\b"),
        ("nghỉ hưu", r"\b(hưu trí|lương hưu|nghỉ hưu|tuổi nghỉ hưu)\b"),
        ("trợ cấp thôi việc / thất nghiệp", r"\b(trợ cấp thôi việc|mất việc|thất nghiệp)\b"),
    ]

    @classmethod
    def extract(cls, query: str) -> ExtractedFactProfile:
        q_lower = query.lower()

        # 1. Subjects
        subjects = []
        for name, pattern in cls.SUBJECT_PATTERNS:
            if re.search(pattern, q_lower):
                subjects.append(name)
        if not subjects:
            subjects.append("người lao động (mặc định)")

        # 2. Actions & Events
        actions = []
        for name, pattern in cls.ACTION_PATTERNS:
            if re.search(pattern, q_lower):
                actions.append(name)

        # 3. Numbers & Durations
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?(?:\s*(?:ngày|tháng|năm|giờ|%|triệu|đồng))?\b", q_lower)

        # 4. Legal Issues
        issues = []
        if any(w in q_lower for w in ["điều kiện", "được không", "có được", "quyền", "trường hợp nào"]):
            issues.append("Điều kiện được hưởng / Quyền thực hiện hành vi")
        if any(w in q_lower for w in ["mức", "bao nhiêu", "tính như thế nào", "tiền", "lương", "%", "phần trăm"]):
            issues.append("Mức hưởng / Tỷ lệ tiền lương hoặc trợ cấp")
        if any(w in q_lower for w in ["bao lâu", "thời hạn", "thời gian", "báo trước", "mấy ngày", "mấy tháng"]):
            issues.append("Thời hạn áp dụng / Thời hạn báo trước / Thời gian hưởng")
        if any(w in q_lower for w in ["trách nhiệm", "nghĩa vụ", "có phải", "bắt buộc"]):
            issues.append("Trách nhiệm và nghĩa vụ pháp lý của các bên")
        if not issues:
            issues.append("Xác định quyền và nghĩa vụ theo quy định pháp luật")

        # 5. Missing Facts Detection (Phát hiện dữ kiện còn thiếu)
        missing = []
        if "thử việc" in actions and not any(w in q_lower for w in ["hợp đồng lao động", "hợp đồng thử việc riêng"]):
            missing.append("Hình thức giao kết (thỏa thuận thử việc trong HĐLĐ hay lập Hợp đồng thử việc riêng)")
        if "nghỉ ốm đau" in actions and not any(w in q_lower for w in ["dài ngày", "bình thường", "bệnh viện"]):
            missing.append("Tính chất bệnh (ốm đau thông thường hay mắc bệnh cần chữa trị dài ngày; có giấy xác nhận của cơ sở y tế hay không)")
        if "đơn phương chấm dứt" in actions and not any(w in q_lower for w in ["xác định thời hạn", "không xác định"]):
            missing.append("Loại hợp đồng lao động đang thực hiện (xác định thời hạn hay không xác định thời hạn)")
        if "nghỉ hưu" in actions and not any(w in q_lower for w in ["nam", "nữ", "tuổi", "đóng"]):
            missing.append("Giới tính, năm sinh, môi trường làm việc và thời gian thực tế đã đóng BHXH")

        # 6. Temporal Clues
        temporal = []
        if any(w in q_lower for w in ["2024", "2025", "2026", "hiện nay", "sau 01/7/2025", "mới nhất"]):
            temporal.append("Người dùng quan tâm quy định hiện hành hoặc quy định có hiệu lực trong tương lai")

        return ExtractedFactProfile(
            subjects=subjects,
            actions=actions,
            numbers_and_durations=numbers,
            legal_issues=issues,
            missing_facts=missing,
            temporal_clues=temporal
        )


class FactToLawPromptBuilder:
    """
    Constructs high-precision, syllogistic prompts optimized for local Qwen2.5-1.5B on CPU.
    """

    @classmethod
    def build_context_text(cls, chunks: List[EnrichedChunk]) -> Tuple[str, List[str]]:
        context_parts = []
        temporal_notes = []
        seen_cids = set()
        ordered_chunks = []

        for c in chunks:
            if c.chunk_id not in seen_cids:
                seen_cids.add(c.chunk_id)
                ordered_chunks.append(c)

        # Select top 5 chunks for compact CPU context
        selected_chunks = ordered_chunks[:5]

        for idx, c in enumerate(selected_chunks, 1):
            doc_name = c.document_name
            doc_num = c.document_number
            art = c.article
            clause = c.clause
            page = c.page_start

            # Temporal information from DOCUMENTS_CONFIG
            date_info = ""
            if "18/VBHN" in doc_num:
                date_info = " [VBHN có hiệu lực từ 01/01/2021]"
            elif "41/2024" in doc_num:
                date_info = " [Luật BHXH 2024 có hiệu lực từ 01/07/2025]"
                t_msg = "Luật BHXH 2024 (số 41/2024/QH15) có hiệu lực thi hành từ ngày 01/07/2025."
                if t_msg not in temporal_notes:
                    temporal_notes.append(t_msg)

            header = f"--- NGUỒN {idx}: {doc_name} ({doc_num}){date_info} | {art} | {clause} (Trang {page}) ---"
            context_parts.append(f"{header}\n{c.text.strip()}\n")

        return "\n".join(context_parts), temporal_notes

    @classmethod
    def build_system_prompt(cls) -> str:
        return (
            "Bạn là Chuyên gia Tư vấn Pháp lý Lao động & Bảo hiểm xã hội Việt Nam.\n"
            "NGUYÊN TẮC SUY LUẬN TAM ĐOẠN LUẬN (FACT-TO-LAW REASONING):\n"
            "1. Căn cứ quy phạm: Chỉ dựa vào VĂN BẢN ĐƯỢC CUNG CẤP. Không tự nhớ, không bịa đặt số Điều, tỷ lệ % hoặc thời hạn.\n"
            "2. Đối chiếu dữ kiện: Chỉ áp dụng điều luật khi dữ kiện của người hỏi thỏa mãn ĐẦY ĐỦ điều kiện trong luật. Nếu dữ kiện thiếu, phải nêu rõ 'Nếu trường hợp A... Nếu trường hợp B...'.\n"
            "3. Ngoại lệ: Bắt buộc nêu rõ các trường hợp ngoại lệ hoặc loại trừ nếu điều luật có quy định.\n"
            "4. Tính ngắn gọn: Trình bày súc tích, mạch lạc (dưới 350 tokens), không chép lại cả trang văn bản."
        )

    @classmethod
    def build_user_prompt(cls, query: str, context_text: str, fact_profile: ExtractedFactProfile, temporal_notes: List[str]) -> str:
        missing_facts_hint = ""
        if fact_profile.missing_facts:
            missing_facts_hint = f"\nLƯU Ý DỮ KIỆN CÓ THỂ THIẾU TỪ CÂU HỎI: {'; '.join(fact_profile.missing_facts)}"

        temporal_hint = ""
        if temporal_notes:
            temporal_hint = f"\nLƯU Ý THỜI ĐIỂM HIỆU LỰC: {'; '.join(temporal_notes)}"

        return (
            f"VĂN BẢN PHÁP LUẬT THAM KHẢO:\n"
            f"{context_text}\n"
            f"CÂU HỎI NGƯỜI DÙNG:\n{query}\n"
            f"CÁC VẤN ĐỀ PHÁP LÝ CẦN GIẢI QUYẾT: {', '.join(fact_profile.legal_issues)}"
            f"{missing_facts_hint}"
            f"{temporal_hint}\n\n"
            f"HÃY PHÂN TÍCH VÀ TRẢ LỜI THEO CẤU TRÚC 4 PHẦN CHUẨN XÁC:\n"
            f"- KẾT LUẬN: (Trả lời thẳng vào câu hỏi một cách dứt khoát, chính xác theo dữ kiện)\n"
            f"- CĂN CỨ PHÁP LÝ: (Ghi rõ Tên luật, Điều mấy, Khoản mấy theo đúng nguồn trên)\n"
            f"- ĐIỀU KIỆN VÀ MỨC ÁP DỤNG: (Tỷ lệ %, số ngày/tháng, điều kiện tiên quyết và đối chiếu với dữ kiện)\n"
            f"- LƯU Ý/NGOẠI LỆ: (Các ngoại lệ luật định, lưu ý về thời điểm hiệu lực hoặc thông tin người dùng cần bổ sung)"
        )
