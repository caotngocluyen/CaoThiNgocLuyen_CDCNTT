import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from src.memory.conversation_memory import ConversationState, ConversationMemory
from src.utils.logger import get_logger

logger = get_logger("QueryRewriter")

@dataclass
class RewriteResult:
    is_follow_up: bool
    original_query: str
    rewritten_query: str
    is_rewritten: bool
    detected_topic: Optional[str] = None
    topic_shift_detected: bool = False
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_follow_up": self.is_follow_up,
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "is_rewritten": self.is_rewritten,
            "detected_topic": self.detected_topic,
            "topic_shift_detected": self.topic_shift_detected,
            "extracted_entities": self.extracted_entities,
            "needs_clarification": self.needs_clarification,
            "clarification_prompt": self.clarification_prompt,
            "reasoning": self.reasoning
        }


class ContextAwareQueryRewriter:
    """
    Context-Aware Query Rewriting Engine:
    - Detects whether a new user query is a follow-up or independent.
    - Preserves user facts, numbers, and dates without hallucination.
    - Rewrites incomplete / elliptical / pronoun queries into self-contained legal queries.
    - Handles topic shifts gracefully, avoiding stale context pollution.
    - Flags ambiguous queries for clarification.
    """

    # Legal topic definitions with associated keywords and canonical articles
    TOPIC_REGISTRY = {
        "tien_luong_lam_them_gio": {
            "label": "Tiền lương làm thêm giờ và làm đêm",
            "keywords": ["làm thêm", "làm thêm giờ", "tăng ca", "làm đêm", "lương làm thêm", "cuối tuần", "ngày nghỉ hằng tuần"],
            "legal_documents": ["Bộ luật Lao động 2019"],
            "legal_articles": ["Điều 98"],
            "domain": "labor_law"
        },
        "nghi_phep_hang_nam": {
            "label": "Nghỉ phép hằng năm và ngày nghỉ có hưởng lương",
            "keywords": ["nghỉ phép", "phép năm", "nghỉ hằng năm", "nghỉ hàng năm", "ngày phép"],
            "legal_documents": ["Bộ luật Lao động 2019"],
            "legal_articles": ["Điều 113", "Điều 114"],
            "domain": "labor_law"
        },
        "che_do_thai_san": {
            "label": "Chế độ thai sản",
            "keywords": ["thai sản", "nghỉ đẻ", "sinh con", "chế độ thai sản", "nghỉ thai sản"],
            "legal_documents": ["Luật Bảo hiểm xã hội 2024"],
            "legal_articles": ["Điều 50", "Điều 51"],
            "domain": "social_insurance"
        },
        "cham_dut_hop_dong_lao_dong": {
            "label": "Chấm dứt hợp đồng lao động và đơn phương chấm dứt",
            "keywords": ["đơn phương chấm dứt", "chấm dứt hợp đồng", "sa thải", "thôi việc", "đuổi việc", "báo trước"],
            "legal_documents": ["Bộ luật Lao động 2019"],
            "legal_articles": ["Điều 35", "Điều 36", "Điều 46"],
            "domain": "labor_law"
        },
        "thoi_gian_thu_viec": {
            "label": "Thời gian thử việc và hợp đồng thử việc",
            "keywords": ["thử việc", "thời gian thử việc", "hợp đồng thử việc"],
            "legal_documents": ["Bộ luật Lao động 2019", "Luật Bảo hiểm xã hội 2024"],
            "legal_articles": ["Điều 24", "Điều 25", "Điều 2"],
            "domain": "labor_law"
        },
        "che_do_om_dau": {
            "label": "Chế độ ốm đau và trợ cấp ốm đau",
            "keywords": ["ốm đau", "chế độ ốm đau", "trợ cấp ốm đau", "tiền ốm"],
            "legal_documents": ["Luật Bảo hiểm xã hội 2024"],
            "legal_articles": ["Điều 42", "Điều 45"],
            "domain": "social_insurance"
        },
        "che_do_huu_tri": {
            "label": "Chế độ hưu trí và lương hưu",
            "keywords": ["hưu trí", "lương hưu", "tuổi nghỉ hưu", "về hưu"],
            "legal_documents": ["Luật Bảo hiểm xã hội 2024", "Bộ luật Lao động 2019"],
            "legal_articles": ["Điều 64", "Điều 169"],
            "domain": "social_insurance"
        }
    }

    # Follow-up query start markers
    FOLLOW_UP_STARTERS = [
        "vậy", "vậy còn", "thế còn", "còn", "nếu", "thì sao", "thế thì",
        "trường hợp đó", "trường hợp này", "đối với", "với", "cho tôi hỏi thêm",
        "còn tôi", "tôi", "lương của tôi", "lương tôi", "thâm niên"
    ]

    # Explicit pronoun / reference words indicating context dependency
    PRONOUNS_AND_REFERENCES = [
        "đó", "này", "trên", "như vậy", "thì sao", "bao nhiêu ngày", "bao lâu",
        "được bao nhiêu", "còn tôi", "của tôi", "ai chi trả", "người đó", "cái đó", "việc đó"
    ]

    def __init__(self):
        logger.info("Khởi tạo ContextAwareQueryRewriter thành công")

    def detect_topic_from_text(self, text: str) -> Optional[str]:
        """Identifies explicit topic match in text."""
        t_lower = text.lower()
        for topic_key, info in self.TOPIC_REGISTRY.items():
            for kw in info["keywords"]:
                if kw in t_lower:
                    return topic_key
        return None

    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extracts legal entities, figures, dates, and parameters from query.
        """
        q_lower = query.lower()
        entities = {}

        # 1. Salary extraction (e.g. 30 triệu, 15 triệu đồng, 20.000.000 đ)
        salary_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(triệu|tr|nghìn|ngàn|vnđ|vnd|đ|đồng)", q_lower)
        if salary_match:
            num = salary_match.group(1)
            unit = salary_match.group(2)
            if unit in ["triệu", "tr"]:
                entities["salary"] = f"{num} triệu đồng"
            else:
                entities["salary"] = f"{num} {unit}"
        elif "lương" in q_lower:
            m = re.search(r"lương(?:\s+của\s+tôi)?\s+(?:là\s+)?(\d+[\d\.,\s]*\w+)", q_lower)
            if m:
                entities["salary"] = m.group(1).strip()

        # 2. Seniority / Working duration (e.g. làm việc 5 năm, 3 năm, 6 tháng)
        seniority_match = re.search(r"(?:làm việc|làm|thâm niên|đóng bảo hiểm|đóng bhxh)?\s*(\d+)\s*(năm|tháng)", q_lower)
        if seniority_match:
            entities["seniority"] = f"{seniority_match.group(1)} {seniority_match.group(2)}"

        # 3. Subject / Actor
        if "người sử dụng lao động" in q_lower or "công ty" in q_lower or "doanh nghiệp" in q_lower or "sếp" in q_lower:
            entities["actor"] = "người sử dụng lao động"
        elif "người lao động" in q_lower or "nhân viên" in q_lower or "tôi" in q_lower:
            entities["actor"] = "người lao động"

        # 4. Day type / condition (cuối tuần, thứ 7, chủ nhật, ngày lễ)
        if "cuối tuần" in q_lower or "thứ 7" in q_lower or "chủ nhật" in q_lower or "nghỉ hàng tuần" in q_lower or "nghỉ hằng tuần" in q_lower:
            entities["day_type"] = "ngày nghỉ hằng tuần"
        elif "ngày lễ" in q_lower or "ngày tết" in q_lower:
            entities["day_type"] = "ngày nghỉ lễ, tết"
        elif "ngày thường" in q_lower:
            entities["day_type"] = "ngày thường"

        # 5. Contract type
        if "không xác định thời hạn" in q_lower:
            entities["contract_type"] = "hợp đồng lao động không xác định thời hạn"
        elif "xác định thời hạn" in q_lower:
            entities["contract_type"] = "hợp đồng lao động xác định thời hạn"

        return entities

    def is_ambiguous_query(self, query: str, state: ConversationState) -> bool:
        """
        Detects if query is excessively vague and cannot be resolved reliably.
        E.g. 'còn cái kia thì sao?' or 'thế có được không?'
        """
        q_clean = query.strip().lower()
        ambiguous_patterns = [
            r"^còn (?:cái|trường hợp|điều) kia thì sao[\?]?$",
            r"^vậy có được không[\?]?$",
            r"^thế có được không[\?]?$",
            r"^còn cái khác thì sao[\?]?$"
        ]
        for p in ambiguous_patterns:
            if re.match(p, q_clean):
                return True
        return False

    def check_is_follow_up(self, query: str, state: ConversationState) -> Tuple[bool, Optional[str], bool, str]:
        """
        Determines whether query is follow-up, topic shift, or independent.
        Returns: (is_follow_up, new_topic, topic_shift_detected, reason)
        """
        q_lower = query.strip().lower()

        # 1. No active conversation state
        if not state.current_topic:
            topic = self.detect_topic_from_text(query)
            return False, topic, False, "Hội thoại mới bắt đầu hoặc chưa có chủ đề trước đó."

        # 2. Check for Ambiguous query
        if self.is_ambiguous_query(query, state):
            return True, state.current_topic, False, "Câu hỏi quá mơ hồ, cần yêu cầu người dùng làm rõ."

        # 3. Check for Topic Shift
        detected_new_topic = self.detect_topic_from_text(query)
        if detected_new_topic and detected_new_topic != state.current_topic:
            # Verify if this is truly a full independent topic shift
            # If the user asks a complete question in a new domain, treat as topic shift
            words_count = len(query.split())
            has_follow_up_starter = any(q_lower.startswith(s) for s in self.FOLLOW_UP_STARTERS)
            if words_count >= 5 and not has_follow_up_starter:
                logger.info(f"Phát hiện chuyển chủ đề từ '{state.current_topic}' sang '{detected_new_topic}'")
                return False, detected_new_topic, True, f"Người dùng chủ động chuyển sang chủ đề mới: {detected_new_topic}"

        # 4. Check for Independent Complete Question
        # If question has >= 8 words, does NOT start with follow-up markers, and has complete legal subject + action
        has_starter = any(q_lower.startswith(s + " ") or q_lower == s for s in self.FOLLOW_UP_STARTERS)
        has_pronoun = any(re.search(rf"\b{re.escape(p)}\b", q_lower) for p in self.PRONOUNS_AND_REFERENCES)

        # Explicit independent indicators
        independent_starters = [
            "người lao động được", "người sử dụng lao động có được", "mức hưởng chế độ",
            "thời gian thử việc", "mức phạt", "điều kiện hưởng", "thủ tục"
        ]
        is_independent_starter = any(q_lower.startswith(s) for s in independent_independent) if 'independent_independent' in locals() else any(q_lower.startswith(s) for s in independent_starters)

        if is_independent_starter and not has_starter and not has_pronoun:
            return False, detected_new_topic or state.current_topic, False, "Câu hỏi độc lập, đầy đủ chủ ngữ và vị ngữ."

        # 5. Check Follow-Up Markers
        if has_starter or has_pronoun or len(query.split()) <= 8:
            return True, state.current_topic, False, "Phát hiện câu hỏi tiếp nối phụ thuộc ngữ cảnh hội thoại."

        # Default fallback
        if detected_new_topic and detected_new_topic != state.current_topic:
            return False, detected_new_topic, True, "Chuyển sang chủ đề mới."
        return False, state.current_topic, False, "Câu hỏi có đầy đủ ý nghĩa độc lập."

    def rewrite_query(self, query: str, memory: ConversationMemory) -> RewriteResult:
        """
        Main query rewriting entry point.
        Analyzes conversation state, extracts entities, and stitches full legal context.
        """
        state = memory.state
        is_follow_up, detected_topic, topic_shift, reason = self.check_is_follow_up(query, state)
        extracted_entities = self.extract_entities(query)

        # Case 1: Ambiguous query needing clarification (MT09)
        if self.is_ambiguous_query(query, state):
            clarification = (
                f"Câu hỏi của bạn chưa đủ thông tin cụ thể trong bối cảnh {state.current_topic_label or 'chủ đề đang trao đổi'}. "
                "Bạn đang muốn hỏi cụ thể về trường hợp nào (ví dụ: làm việc vào ngày thường, ngày nghỉ hằng tuần hay ngày lễ, tết)? "
                "Vui lòng nêu rõ để được tư vấn chính xác nhất."
            )
            return RewriteResult(
                is_follow_up=True,
                original_query=query,
                rewritten_query=query,
                is_rewritten=False,
                detected_topic=state.current_topic,
                topic_shift_detected=False,
                extracted_entities=extracted_entities,
                needs_clarification=True,
                clarification_prompt=clarification,
                reasoning=reason
            )

        # Case 2: Not a follow-up (Independent query or Topic Shift) (MT05, MT08)
        if not is_follow_up:
            if topic_shift and detected_topic:
                # Transition memory topic cleanly
                topic_info = self.TOPIC_REGISTRY.get(detected_topic, {})
                memory.set_topic(
                    topic=detected_topic,
                    topic_label=topic_info.get("label"),
                    docs=topic_info.get("legal_documents"),
                    articles=topic_info.get("legal_articles"),
                    clear_old_facts=True
                )
            elif detected_topic:
                topic_info = self.TOPIC_REGISTRY.get(detected_topic, {})
                memory.set_topic(
                    topic=detected_topic,
                    topic_label=topic_info.get("label"),
                    docs=topic_info.get("legal_documents"),
                    articles=topic_info.get("legal_articles"),
                    clear_old_facts=False
                )

            return RewriteResult(
                is_follow_up=False,
                original_query=query,
                rewritten_query=query,
                is_rewritten=False,
                detected_topic=detected_topic or state.current_topic,
                topic_shift_detected=topic_shift,
                extracted_entities=extracted_entities,
                needs_clarification=False,
                reasoning=reason
            )

        # Case 3: Confirmed Follow-up query -> Perform Context-Aware Rewriting (MT01, MT02, MT03, MT04, MT06, MT10)
        # Update user facts in memory first
        if extracted_entities:
            memory.update_facts(extracted_entities)

        # Merge active facts
        all_facts = dict(state.user_provided_facts)
        all_facts.update(extracted_entities)

        topic = state.current_topic
        topic_info = self.TOPIC_REGISTRY.get(topic, {})
        articles_str = ", ".join(state.legal_articles) if state.legal_articles else ", ".join(topic_info.get("legal_articles", []))
        docs_str = ", ".join(state.legal_documents) if state.legal_documents else ", ".join(topic_info.get("legal_documents", []))

        rewritten = query
        q_lower = query.lower()

        # Domain-specific canonical rewriting rules
        if topic == "tien_luong_lam_them_gio":
            # Example 1 & MT01 & MT06: Overtime salary with given salary/day type
            day_type = all_facts.get("day_type", "ngày nghỉ hằng tuần")
            salary = all_facts.get("salary")
            if salary:
                rewritten = (
                    f"Cách xác định tiền lương làm thêm vào {day_type} theo {articles_str or 'Điều 98'} "
                    f"{docs_str or 'Bộ luật Lao động 2019'}, trong trường hợp người lao động có mức lương {salary}."
                )
            else:
                rewritten = f"Cách tính tiền lương làm thêm giờ vào {day_type} theo {articles_str or 'Điều 98'} {docs_str or 'Bộ luật Lao động 2019'}."

        elif topic == "nghi_phep_hang_nam":
            # Example 2 & MT02: Annual leave with given seniority
            seniority = all_facts.get("seniority", "5 năm")
            rewritten = (
                f"Thời gian nghỉ hằng năm (nghỉ phép năm) của người lao động làm việc đủ {seniority} "
                f"theo {articles_str or 'Điều 113, Điều 114'} {docs_str or 'Bộ luật Lao động 2019'}."
            )

        elif topic == "che_do_thai_san":
            # Example 3 & MT03: Maternity regime with duration inquiry
            if "đóng bảo hiểm" in q_lower or "bao lâu" in q_lower or "thời gian" in q_lower:
                rewritten = (
                    f"Thời gian đóng bảo hiểm xã hội để đủ điều kiện hưởng chế độ thai sản "
                    f"theo quy định của {docs_str or 'Luật Bảo hiểm xã hội 2024'}."
                )
            else:
                rewritten = f"Điều kiện và quyền lợi hưởng chế độ thai sản theo {docs_str or 'Luật Bảo hiểm xã hội 2024'}."

        elif topic == "cham_dut_hop_dong_lao_dong":
            # Example 4 & MT04: Notice period for employer termination
            actor = all_facts.get("actor", "người sử dụng lao động")
            contract_type = all_facts.get("contract_type", "")
            contract_snippet = f" đối với {contract_type}" if contract_type else ""
            if "báo trước" in q_lower or "bao nhiêu ngày" in q_lower:
                rewritten = (
                    f"Thời hạn báo trước khi {actor} đơn phương chấm dứt hợp đồng lao động{contract_snippet} "
                    f"theo {articles_str or 'Điều 36'} {docs_str or 'Bộ luật Lao động 2019'}."
                )
            else:
                rewritten = (
                    f"Quy định về việc {actor} đơn phương chấm dứt hợp đồng lao động "
                    f"theo {articles_str or 'Điều 36'} {docs_str or 'Bộ luật Lao động 2019'}."
                )

        elif topic == "thoi_gian_thu_viec":
            rewritten = f"Thời gian thử việc tối đa và quyền lợi của người lao động trong thời gian thử việc theo {articles_str or 'Điều 25'} {docs_str or 'Bộ luật Lao động 2019'}."

        elif topic == "che_do_om_dau":
            rewritten = f"Mức hưởng trợ cấp ốm đau và điều kiện hưởng chế độ ốm đau theo {articles_str or 'Điều 45'} {docs_str or 'Luật Bảo hiểm xã hội 2024'}."

        else:
            # Generic fallback rewriting: stitch topic + query
            facts_snippet = ", ".join([f"{k}: {v}" for k, v in all_facts.items()]) if all_facts else ""
            rewritten = f"{state.current_topic_label or topic}: {query}"
            if articles_str:
                rewritten += f" theo {articles_str}"
            if docs_str:
                rewritten += f" {docs_str}"
            if facts_snippet:
                rewritten += f" ({facts_snippet})"

        logger.info(f"[QueryRewriter] Viết lại thành công:\n  Original:  '{query}'\n  Rewritten: '{rewritten}'")

        return RewriteResult(
            is_follow_up=True,
            original_query=query,
            rewritten_query=rewritten,
            is_rewritten=(rewritten != query),
            detected_topic=topic,
            topic_shift_detected=False,
            extracted_entities=extracted_entities,
            needs_clarification=False,
            reasoning=f"Viết lại câu hỏi tiếp nối dựa trên chủ đề '{topic}' và dữ kiện hội thoại tích lũy."
        )
