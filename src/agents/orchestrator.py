import time
import psutil
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from config import (
    RETRIEVAL_TOP_K,
    RETRIEVAL_CANDIDATE_POOL,
    PARENT_CHILD_EXPAND,
    MAX_RETRY_ATTEMPTS
)
from src.agents.intent_agent import IntentAgent, IntentResult
from src.agents.retrieval_agent import RetrievalAgent, RetrievalContext
from src.agents.legal_analysis_agent import LegalAnalysisAgent, LegalAnalysisResult
from src.agents.validation_agent import ValidationAgent, ValidationResult
from src.agents.response_agent import ResponseAgent, FinalResponse
from src.memory.conversation_memory import (
    ConversationMemory,
    ConversationState,
    SessionManager
)
from src.memory.query_rewriter import ContextAwareQueryRewriter, RewriteResult
from src.utils.logger import get_logger

logger = get_logger("LegalOrchestrator")

@dataclass
class StepTiming:
    rewriting_time: float = 0.0
    intent_time: float = 0.0
    retrieval_time: float = 0.0
    analysis_time: float = 0.0
    validation_time: float = 0.0
    response_time: float = 0.0
    total_time: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class SystemResourceUsage:
    process_ram_before_mb: float = 0.0
    process_ram_after_mb: float = 0.0
    process_ram_delta_mb: float = 0.0
    system_ram_used_gb: float = 0.0
    system_ram_total_gb: float = 0.0
    system_ram_percent: float = 0.0

    # Backwards compatibility properties
    @property
    def ram_before_gb(self) -> float:
        return self.system_ram_used_gb

    @property
    def ram_after_gb(self) -> float:
        return self.system_ram_used_gb

    @property
    def ram_delta_mb(self) -> float:
        return self.process_ram_delta_mb

    def to_dict(self) -> Dict[str, float]:
        return {
            "process_ram_before_mb": self.process_ram_before_mb,
            "process_ram_after_mb": self.process_ram_after_mb,
            "process_ram_delta_mb": self.process_ram_delta_mb,
            "system_ram_used_gb": self.system_ram_used_gb,
            "system_ram_total_gb": self.system_ram_total_gb,
            "system_ram_percent": self.system_ram_percent
        }


@dataclass
class ChatbotResult:
    question: str
    intent: IntentResult
    retrieval: Optional[RetrievalContext]
    analysis: Optional[LegalAnalysisResult]
    validation: Optional[ValidationResult]
    response: FinalResponse
    timing: StepTiming
    resources: SystemResourceUsage
    retries_count: int = 0
    rewritten_query: Optional[str] = None
    is_rewritten: bool = False
    is_follow_up: bool = False
    session_id: str = "default_session"
    conversation_state: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "rewritten_query": self.rewritten_query,
            "is_rewritten": self.is_rewritten,
            "is_follow_up": self.is_follow_up,
            "session_id": self.session_id,
            "intent": self.intent.to_dict(),
            "retrieval": self.retrieval.to_dict() if self.retrieval else None,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "response": self.response.to_dict(),
            "timing": self.timing.to_dict(),
            "resources": self.resources.to_dict(),
            "retries_count": self.retries_count,
            "conversation_state": self.conversation_state
        }


class LegalAgentOrchestrator:
    """
    Main Orchestrator for Phase 3 Agentic Legal Consultation Pipeline with Multi-Turn Memory:
    User Question -> [Memory + Query Rewriting] -> Intent Agent -> Retrieval Agent -> Legal Analysis Agent -> Validation Agent -> Response Agent -> [Memory State Update].
    - Guarantees strict session isolation (no cross-talk).
    - Rewrites context-dependent follow-up questions while leaving independent questions untouched.
    - Manages controlled bounded retries.
    - Monitors CPU, RAM, and step latency.
    """

    def __init__(
        self,
        intent_agent: Optional[IntentAgent] = None,
        retrieval_agent: Optional[RetrievalAgent] = None,
        analysis_agent: Optional[LegalAnalysisAgent] = None,
        validation_agent: Optional[ValidationAgent] = None,
        response_agent: Optional[ResponseAgent] = None,
        query_rewriter: Optional[ContextAwareQueryRewriter] = None,
        session_manager: Optional[SessionManager] = None,
        max_retries: int = MAX_RETRY_ATTEMPTS
    ):
        logger.info("Đang khởi tạo các Agent trong hệ thống Orchestrator...")
        self.intent_agent = intent_agent or IntentAgent()
        self.retrieval_agent = retrieval_agent or RetrievalAgent()
        self.analysis_agent = analysis_agent or LegalAnalysisAgent()
        self.validation_agent = validation_agent or ValidationAgent()
        self.response_agent = response_agent or ResponseAgent()
        self.query_rewriter = query_rewriter or ContextAwareQueryRewriter()
        self.session_manager = session_manager or SessionManager()
        self.max_retries = max_retries
        logger.info("LegalAgentOrchestrator sẵn sàng phục vụ!")

    def _get_process_ram_mb(self) -> float:
        return psutil.Process().memory_info().rss / (1024 ** 2)

    def _get_system_ram_gb(self) -> float:
        return psutil.virtual_memory().used / (1024 ** 3)

    def process_query(self, user_question: str, session_id: str = "default_session") -> ChatbotResult:
        """
        Executes end-to-end agentic workflow with multi-turn memory support, logging, and metric tracking.
        """
        t_start_total = time.time()
        proc_ram_before = self._get_process_ram_mb()
        timing = StepTiming()
        retries_count = 0

        # Retrieve isolated session memory
        memory = self.session_manager.get_or_create_memory(session_id)
        logger.info(f"=== [Session {session_id}] BẮT ĐẦU XỬ LÝ CÂU HỎI: '{user_question}' ===")

        # Step 0: Context-Aware Query Rewriting & Follow-up Analysis
        t0 = time.time()
        rewrite_res = self.query_rewriter.rewrite_query(user_question, memory)
        timing.rewriting_time = time.time() - t0
        logger.info(
            f"[QueryRewriter] FollowUp: {rewrite_res.is_follow_up}, Rewritten: {rewrite_res.is_rewritten} "
            f"({timing.rewriting_time*1000:.1f}ms)"
        )

        # Handle Ambiguous query requiring clarification (MT09)
        if rewrite_res.needs_clarification:
            timing.total_time = time.time() - t_start_total
            proc_ram_after = self._get_process_ram_mb()
            vm = psutil.virtual_memory()
            resources = SystemResourceUsage(
                process_ram_before_mb=round(proc_ram_before, 1),
                process_ram_after_mb=round(proc_ram_after, 1),
                process_ram_delta_mb=round(proc_ram_after - proc_ram_before, 1),
                system_ram_used_gb=round(vm.used / (1024**3), 2),
                system_ram_total_gb=round(vm.total / (1024**3), 2),
                system_ram_percent=vm.percent
            )
            clarification_response = FinalResponse(
                conclusion=rewrite_res.clarification_prompt or "Vui lòng cung cấp thêm thông tin cụ thể.",
                legal_basis=[],
                explanation="Câu hỏi cần được làm rõ thêm trong ngữ cảnh hội thoại hiện tại.",
                important_notes=["Vui lòng nêu rõ trường hợp cụ thể bạn đang muốn tra cứu."],
                formatted_markdown=f"### YÊU CẦU LÀM RÕ THÔNG TIN\n\n{rewrite_res.clarification_prompt}\n",
                confidence_level="TRUNG_BÌNH",
                domain_tag="CLARIFICATION",
                is_answerable=False
            )
            dummy_intent = IntentResult(
                domain=memory.state.current_topic or "general",
                is_in_scope=True,
                raw_query=user_question,
                normalized_query=user_question,
                expanded_query=user_question,
                explanation="Yêu cầu làm rõ thông tin bổ sung"
            )
            return ChatbotResult(
                question=user_question,
                rewritten_query=None,
                is_rewritten=False,
                is_follow_up=True,
                session_id=session_id,
                intent=dummy_intent,
                retrieval=None,
                analysis=None,
                validation=None,
                response=clarification_response,
                timing=timing,
                resources=resources,
                retries_count=0,
                conversation_state=memory.state.to_dict()
            )

        # Target query for Intent and Retrieval
        effective_query = rewrite_res.rewritten_query if rewrite_res.is_rewritten else user_question

        # Step 1: Intent Agent
        t0 = time.time()
        intent = self.intent_agent.classify_intent(effective_query)
        timing.intent_time = time.time() - t0
        logger.info(f"[IntentAgent] Domain: {intent.domain}, InScope: {intent.is_in_scope} ({timing.intent_time*1000:.1f}ms)")

        # Fast exit if Out of Scope
        if not intent.is_in_scope:
            t0 = time.time()
            response = self.response_agent.format_response(intent, None, None, None)
            timing.response_time = time.time() - t0
            timing.total_time = time.time() - t_start_total

            proc_ram_after = self._get_process_ram_mb()
            vm = psutil.virtual_memory()
            resources = SystemResourceUsage(
                process_ram_before_mb=round(proc_ram_before, 1),
                process_ram_after_mb=round(proc_ram_after, 1),
                process_ram_delta_mb=round(proc_ram_after - proc_ram_before, 1),
                system_ram_used_gb=round(vm.used / (1024**3), 2),
                system_ram_total_gb=round(vm.total / (1024**3), 2),
                system_ram_percent=vm.percent
            )
            # Record turn in memory
            memory.add_turn(
                user_query=user_question,
                rewritten_query=rewrite_res.rewritten_query if rewrite_res.is_rewritten else None,
                bot_response=response.conclusion or response.formatted_markdown,
                intent_domain=intent.domain,
                response_summary=response.conclusion
            )
            return ChatbotResult(
                question=user_question,
                rewritten_query=rewrite_res.rewritten_query if rewrite_res.is_rewritten else None,
                is_rewritten=rewrite_res.is_rewritten,
                is_follow_up=rewrite_res.is_follow_up,
                session_id=session_id,
                intent=intent,
                retrieval=None,
                analysis=None,
                validation=None,
                response=response,
                timing=timing,
                resources=resources,
                retries_count=0,
                conversation_state=memory.state.to_dict()
            )

        # Step 2: Retrieval Agent
        t0 = time.time()
        retrieval = self.retrieval_agent.retrieve(
            query=intent.normalized_query,
            expanded_query=intent.expanded_query,
            top_k=RETRIEVAL_TOP_K,
            candidate_pool=RETRIEVAL_CANDIDATE_POOL,
            force_expand=PARENT_CHILD_EXPAND
        )
        timing.retrieval_time = time.time() - t0
        logger.info(f"[RetrievalAgent] Chunks retrieved: {retrieval.total_retrieved} ({timing.retrieval_time:.2f}s)")

        # Step 3: Legal Analysis Agent (Local LLM)
        t0 = time.time()
        analysis = self.analysis_agent.analyze(intent.normalized_query, retrieval)
        timing.analysis_time = time.time() - t0
        logger.info(f"[LegalAnalysisAgent] Status: {analysis.status}, Tokens: {analysis.completion_tokens} ({timing.analysis_time:.2f}s)")

        # Step 4: Validation Agent
        t0 = time.time()
        validation = self.validation_agent.validate(analysis, retrieval)
        timing.validation_time = time.time() - t0
        logger.info(f"[ValidationAgent] Status: {validation.validation_status} ({timing.validation_time*1000:.1f}ms)")

        # Bounded Retry Loop: if validation failed and can retry, attempt 1 broadened search
        if (validation.can_retry or not analysis.is_sufficient) and retries_count < self.max_retries:
            logger.warning("[Orchestrator] Kích hoạt RETRY có giới hạn: mở rộng candidate pool và top_k...")
            retries_count += 1
            t_retry_start = time.time()

            retrieval_retry = self.retrieval_agent.retrieve(
                query=intent.normalized_query,
                expanded_query=intent.expanded_query,
                top_k=RETRIEVAL_TOP_K + 2,
                candidate_pool=RETRIEVAL_CANDIDATE_POOL + 10,
                force_expand=True
            )
            analysis_retry = self.analysis_agent.analyze(intent.normalized_query, retrieval_retry)
            validation_retry = self.validation_agent.validate(analysis_retry, retrieval_retry)

            if validation_retry.is_valid or analysis_retry.is_sufficient:
                logger.info("[Orchestrator] Retry thành công, sử dụng kết quả mở rộng!")
                retrieval = retrieval_retry
                analysis = analysis_retry
                validation = validation_retry
            else:
                logger.warning("[Orchestrator] Retry hoàn thành nhưng không tìm thêm được căn cứ mới.")

            timing.retrieval_time += (time.time() - t_retry_start)

        # Step 5: Response Agent
        t0 = time.time()
        response = self.response_agent.format_response(intent, retrieval, analysis, validation)
        timing.response_time = time.time() - t0
        logger.info(f"[ResponseAgent] Final response formatted ({timing.response_time*1000:.1f}ms)")

        timing.total_time = time.time() - t_start_total
        proc_ram_after = self._get_process_ram_mb()
        vm = psutil.virtual_memory()
        resources = SystemResourceUsage(
            process_ram_before_mb=round(proc_ram_before, 1),
            process_ram_after_mb=round(proc_ram_after, 1),
            process_ram_delta_mb=round(proc_ram_after - proc_ram_before, 1),
            system_ram_used_gb=round(vm.used / (1024**3), 2),
            system_ram_total_gb=round(vm.total / (1024**3), 2),
            system_ram_percent=vm.percent
        )

        # Step 6: Update Conversation Memory
        extracted_docs = list(set([c.document_name for c in analysis.legal_citations])) if analysis else []
        extracted_arts = list(set([c.article for c in analysis.legal_citations])) if analysis else []

        memory.add_turn(
            user_query=user_question,
            rewritten_query=rewrite_res.rewritten_query if rewrite_res.is_rewritten else None,
            bot_response=response.conclusion or response.formatted_markdown,
            intent_domain=intent.domain,
            legal_documents=extracted_docs,
            legal_articles=extracted_arts,
            extracted_facts=rewrite_res.extracted_entities,
            response_summary=response.conclusion
        )

        # If independent and a topic was identified, update active topic
        if not rewrite_res.is_follow_up and rewrite_res.detected_topic:
            topic_info = self.query_rewriter.TOPIC_REGISTRY.get(rewrite_res.detected_topic, {})
            memory.set_topic(
                topic=rewrite_res.detected_topic,
                topic_label=topic_info.get("label"),
                docs=extracted_docs or topic_info.get("legal_documents"),
                articles=extracted_arts or topic_info.get("legal_articles"),
                clear_old_facts=False
            )

        logger.info(
            f"=== [Session {session_id}] HOÀN TẤT TRONG {timing.total_time:.2f}s | "
            f"Rewriter: {timing.rewriting_time*1000:.1f}ms | Intent: {timing.intent_time*1000:.1f}ms | "
            f"Retrieval: {timing.retrieval_time:.2f}s | Analysis: {timing.analysis_time:.2f}s | "
            f"Validation: {timing.validation_time*1000:.1f}ms | "
            f"RAM Tiến trình: {resources.process_ram_after_mb:.1f} MB (Delta: {resources.process_ram_delta_mb:+.1f} MB) ==="
        )

        return ChatbotResult(
            question=user_question,
            rewritten_query=rewrite_res.rewritten_query if rewrite_res.is_rewritten else None,
            is_rewritten=rewrite_res.is_rewritten,
            is_follow_up=rewrite_res.is_follow_up,
            session_id=session_id,
            intent=intent,
            retrieval=retrieval,
            analysis=analysis,
            validation=validation,
            response=response,
            timing=timing,
            resources=resources,
            retries_count=retries_count,
            conversation_state=memory.state.to_dict()
        )
