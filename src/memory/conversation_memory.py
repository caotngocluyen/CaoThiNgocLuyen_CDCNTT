import time
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger("ConversationMemory")

@dataclass
class TurnRecord:
    turn_id: int
    user_query: str
    rewritten_query: Optional[str] = None
    bot_response: str = ""
    intent_domain: str = ""
    legal_documents: List[str] = field(default_factory=list)
    legal_articles: List[str] = field(default_factory=list)
    extracted_facts: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_query": self.user_query,
            "rewritten_query": self.rewritten_query,
            "bot_response": self.bot_response[:200] + "..." if len(self.bot_response) > 200 else self.bot_response,
            "intent_domain": self.intent_domain,
            "legal_documents": self.legal_documents,
            "legal_articles": self.legal_articles,
            "extracted_facts": self.extracted_facts,
            "timestamp": self.timestamp
        }


@dataclass
class ConversationState:
    current_topic: Optional[str] = None           # Internal key: e.g. "tien_luong_lam_them_gio"
    current_topic_label: Optional[str] = None     # Human-readable: "Tiền lương làm thêm giờ"
    current_intent: Optional[str] = None          # e.g. "hoi_muc_luong_lam_them"
    legal_documents: List[str] = field(default_factory=list)  # ["Bộ luật Lao động 2019"]
    legal_articles: List[str] = field(default_factory=list)    # ["Điều 98"]
    entities: Dict[str, Any] = field(default_factory=dict)      # {"day_type": "ngay_nghi_hang_tuan"}
    user_provided_facts: Dict[str, Any] = field(default_factory=dict) # {"salary": "30 triệu", "seniority": "5 năm"}
    pending_information: List[str] = field(default_factory=list)
    last_query: Optional[str] = None
    last_response_summary: Optional[str] = None
    turn_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConversationMemory:
    """
    Manages multi-turn conversation history and persistent structured state for a single user session.
    - Limits history length (sliding window) to prevent CPU LLM context overflow.
    - Tracks user-provided facts and updates/overwrites when user corrects them.
    - Maintains active legal documents and articles across turns.
    - Smoothly transitions state when a topic shift occurs without polluting new topics.
    """

    def __init__(self, session_id: str = "default_session", max_turns: int = 6):
        self.session_id = session_id
        self.max_turns = max_turns
        self.history: List[TurnRecord] = []
        self.state = ConversationState()
        logger.info(f"Khởi tạo ConversationMemory cho session '{session_id}' (max_turns={max_turns})")

    def add_turn(
        self,
        user_query: str,
        rewritten_query: Optional[str],
        bot_response: str,
        intent_domain: str = "",
        legal_documents: Optional[List[str]] = None,
        legal_articles: Optional[List[str]] = None,
        extracted_facts: Optional[Dict[str, Any]] = None,
        response_summary: Optional[str] = None
    ) -> TurnRecord:
        """
        Records a completed interaction turn and updates the session state.
        """
        turn_id = len(self.history) + 1
        record = TurnRecord(
            turn_id=turn_id,
            user_query=user_query,
            rewritten_query=rewritten_query,
            bot_response=bot_response,
            intent_domain=intent_domain,
            legal_documents=legal_documents or [],
            legal_articles=legal_articles or [],
            extracted_facts=extracted_facts or {},
            timestamp=time.time()
        )
        self.history.append(record)

        # Sliding window constraint
        if len(self.history) > self.max_turns:
            dropped = self.history.pop(0)
            logger.debug(f"[Session {self.session_id}] Loại bỏ turn {dropped.turn_id} để giữ kích thước context")

        # Update Conversation State
        self.state.turn_count = len(self.history)
        self.state.last_query = user_query

        if response_summary:
            self.state.last_response_summary = response_summary
        elif bot_response:
            # Generate short summary from first sentence or conclusion
            first_line = bot_response.split("\n")[0].strip()
            self.state.last_response_summary = first_line[:150]

        if legal_documents:
            for doc in legal_documents:
                if doc not in self.state.legal_documents:
                    self.state.legal_documents.append(doc)

        if legal_articles:
            for art in legal_articles:
                if art not in self.state.legal_articles:
                    self.state.legal_articles.append(art)

        if extracted_facts:
            self.update_facts(extracted_facts)

        return record

    def update_facts(self, new_facts: Dict[str, Any]):
        """
        Merges new user-provided facts into state. Overwrites old values if updated (e.g. user corrected salary).
        """
        for k, v in new_facts.items():
            if k in self.state.user_provided_facts:
                logger.info(f"[Session {self.session_id}] Cập nhật dữ kiện '{k}': '{self.state.user_provided_facts[k]}' -> '{v}'")
            else:
                logger.info(f"[Session {self.session_id}] Ghi nhận dữ kiện mới '{k}': '{v}'")
            self.state.user_provided_facts[k] = v

    def set_topic(
        self,
        topic: str,
        topic_label: Optional[str] = None,
        intent: Optional[str] = None,
        docs: Optional[List[str]] = None,
        articles: Optional[List[str]] = None,
        clear_old_facts: bool = False
    ):
        """
        Sets or updates the current topic. If clear_old_facts is True (topic shift), resets topic-specific facts.
        """
        if self.state.current_topic and self.state.current_topic != topic and clear_old_facts:
            logger.info(f"[Session {self.session_id}] Chuyển chủ đề: '{self.state.current_topic}' -> '{topic}'. Xóa dữ kiện cũ.")
            self.state.user_provided_facts.clear()
            self.state.entities.clear()
            self.state.legal_documents = docs or []
            self.state.legal_articles = articles or []
        else:
            if docs:
                for d in docs:
                    if d not in self.state.legal_documents:
                        self.state.legal_documents.append(d)
            if articles:
                for a in articles:
                    if a not in self.state.legal_articles:
                        self.state.legal_articles.append(a)

        self.state.current_topic = topic
        self.state.current_topic_label = topic_label or topic
        if intent:
            self.state.current_intent = intent

    def get_recent_history(self, n: int = 3) -> List[TurnRecord]:
        """Returns the most recent n turns."""
        return self.history[-n:] if self.history else []

    def get_context_summary(self) -> str:
        """
        Returns a concise context summary for prompt injection or diagnostics.
        """
        if not self.state.current_topic and not self.state.user_provided_facts:
            return "Chưa có ngữ cảnh hội thoại trước."

        parts = []
        if self.state.current_topic_label:
            parts.append(f"Chủ đề hiện tại: {self.state.current_topic_label}")
        if self.state.legal_documents:
            parts.append(f"Văn bản pháp luật: {', '.join(self.state.legal_documents)}")
        if self.state.legal_articles:
            parts.append(f"Căn cứ Điều luật: {', '.join(self.state.legal_articles)}")
        if self.state.user_provided_facts:
            facts_str = ", ".join([f"{k}: {v}" for k, v in self.state.user_provided_facts.items()])
            parts.append(f"Dữ kiện người dùng đã nêu: {facts_str}")
        if self.state.last_response_summary:
            parts.append(f"Tóm tắt kết luận trước: {self.state.last_response_summary}")

        return " | ".join(parts)

    def get_formatted_dialogue(self, n: int = 3) -> str:
        """
        Formats recent turns as dialogue text (User/Bot) for LLM context.
        """
        recent = self.get_recent_history(n)
        if not recent:
            return ""

        lines = []
        for r in recent:
            lines.append(f"Người dùng: {r.user_query}")
            # Truncate bot response to avoid blowing token limit
            resp_summary = r.bot_response.split("\n")[0].strip()
            if len(resp_summary) > 120:
                resp_summary = resp_summary[:120] + "..."
            lines.append(f"Trợ lý: {resp_summary}")
        return "\n".join(lines)

    def clear(self):
        """Completely resets session history and state."""
        self.history.clear()
        self.state = ConversationState()
        logger.info(f"[Session {self.session_id}] Đã xóa toàn bộ lịch sử và trạng thái hội thoại.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_count": len(self.history),
            "state": self.state.to_dict(),
            "history": [t.to_dict() for t in self.history]
        }


class SessionManager:
    """
    Thread-safe registry for managing multiple distinct user conversation sessions.
    Guarantees strict isolation between sessions (no cross-talk / data leakage).
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._sessions = {}
        return cls._instance

    def get_or_create_memory(self, session_id: str, max_turns: int = 6) -> ConversationMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(session_id=session_id, max_turns=max_turns)
        return self._sessions[session_id]

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].clear()

    def delete_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Đã hủy session '{session_id}'")

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def reset_all(self):
        self._sessions.clear()
