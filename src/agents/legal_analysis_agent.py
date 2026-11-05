import re
import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from llama_cpp import Llama

from config import (
    LLM_MODEL_PATH,
    LLM_N_CTX,
    LLM_N_THREADS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS
)
from src.agents.retrieval_agent import EnrichedChunk, RetrievalContext
from src.agents.fact_reasoning import (
    FactExtractor,
    FactToLawPromptBuilder,
    ExtractedFactProfile
)
from src.utils.logger import get_logger

logger = get_logger("LegalAnalysisAgent")

@dataclass
class LegalCitation:
    document_name: str
    document_number: str
    article: str
    clause: str
    page_start: int
    quote_snippet: Optional[str] = None
    chunk_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LegalAnalysisResult:
    status: str                         # "success", "insufficient_evidence", "error"
    is_sufficient: bool
    conclusion: str
    legal_citations: List[LegalCitation] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    rates_and_deadlines: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    extracted_facts: List[str] = field(default_factory=list)
    legal_issues: List[str] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    temporal_notes: List[str] = field(default_factory=list)
    raw_llm_response: str = ""
    inference_time_sec: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_sufficient": self.is_sufficient,
            "conclusion": self.conclusion,
            "legal_citations": [c.to_dict() for c in self.legal_citations],
            "conditions": self.conditions,
            "rates_and_deadlines": self.rates_and_deadlines,
            "exceptions": self.exceptions,
            "extracted_facts": self.extracted_facts,
            "legal_issues": self.legal_issues,
            "missing_facts": self.missing_facts,
            "temporal_notes": self.temporal_notes,
            "raw_llm_response": self.raw_llm_response,
            "inference_time_sec": self.inference_time_sec,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens
        }


class LocalLLMManager:
    """Singleton manager for local llama.cpp model instance."""
    _instance: Optional[Llama] = None

    @classmethod
    def get_instance(cls) -> Llama:
        if cls._instance is None:
            logger.info(f"Đang nạp Local LLM từ {LLM_MODEL_PATH} (n_ctx={LLM_N_CTX}, threads={LLM_N_THREADS})...")
            cls._instance = Llama(
                model_path=str(LLM_MODEL_PATH),
                n_ctx=LLM_N_CTX,
                n_threads=LLM_N_THREADS,
                verbose=False
            )
            logger.info("Nạp Local LLM thành công!")
        return cls._instance


class LegalAnalysisAgent:
    """
    Legal Analysis Agent (Phase 4.3 - Fact-to-Law Reasoning):
    - Runs local quantized Qwen2.5-1.5B-Instruct on CPU.
    - Grounds legal reasoning strictly in retrieved official legal chunks.
    - Syllogistic workflow:
      1. Fact Extraction (User facts, subjects, events).
      2. Issue Identification (Core legal claims).
      3. Rule Extraction (Conditions, percentages, deadlines, exceptions).
      4. Fact-to-Law Subsumption (Matching user facts with conditions).
      5. Conclusion & Temporal Awareness (Effective dates, missing facts).
    """

    def __init__(self, llm_instance: Optional[Llama] = None):
        self.llm = llm_instance or LocalLLMManager.get_instance()

    def _build_context_prompt(self, chunks: List[EnrichedChunk]) -> Tuple[str, List[str]]:
        """Formats legal chunks into structured reference text with validity dates."""
        return FactToLawPromptBuilder.build_context_text(chunks)

    def analyze(self, query: str, retrieval_context: RetrievalContext) -> LegalAnalysisResult:
        """
        Analyzes query using Local LLM strictly conditioned on retrieved chunks
        using the Fact-to-Law Syllogism pipeline.
        """
        chunks = retrieval_context.all_chunks
        if not chunks:
            logger.warning("Không có chunks nào từ retrieval, trả về insufficient_evidence")
            return LegalAnalysisResult(
                status="insufficient_evidence",
                is_sufficient=False,
                conclusion="Không tìm thấy văn bản pháp luật phù hợp trong cơ sở dữ liệu để trả lời câu hỏi.",
                inference_time_sec=0.0
            )

        # 1. Fact & Issue Pre-Extraction
        fact_profile = FactExtractor.extract(query)

        # 2. Build Context and Prompts
        context_text, temporal_notes = self._build_context_prompt(chunks)
        system_prompt = FactToLawPromptBuilder.build_system_prompt()
        user_prompt = FactToLawPromptBuilder.build_user_prompt(query, context_text, fact_profile, temporal_notes)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Bắt đầu phân tích pháp lý Fact-to-Law qua Local LLM cho câu hỏi: '{query[:60]}...'")
        t0 = time.time()
        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                temperature=LLM_TEMPERATURE,
                top_p=LLM_TOP_P,
                max_tokens=LLM_MAX_TOKENS
            )
            latency = time.time() - t0
            raw_text = response["choices"][0]["message"]["content"].strip()
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            logger.info(f"Local LLM hoàn thành trong {latency:.2f}s ({completion_tokens} tokens)")

        except Exception as e:
            logger.error(f"Lỗi khi gọi Local LLM: {e}")
            return LegalAnalysisResult(
                status="error",
                is_sufficient=False,
                conclusion=f"Lỗi phân tích mô hình: {str(e)}",
                inference_time_sec=time.time() - t0
            )

        # 3. Parse LLM response into structured result
        return self._parse_llm_response(
            raw_text=raw_text,
            latency=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            chunks=chunks,
            fact_profile=fact_profile,
            temporal_notes=temporal_notes
        )

    def _parse_llm_response(
        self,
        raw_text: str,
        latency: float,
        prompt_tokens: int,
        completion_tokens: int,
        chunks: List[EnrichedChunk],
        fact_profile: Optional[ExtractedFactProfile] = None,
        temporal_notes: Optional[List[str]] = None
    ) -> LegalAnalysisResult:
        """Parses LLM textual output into structured sections and matches citations against chunks."""
        is_sufficient = "CHƯA_ĐỦ_CĂN_CỨ" not in raw_text and "chưa đủ căn cứ" not in raw_text.lower()
        status = "success" if is_sufficient else "insufficient_evidence"

        conclusion = ""
        conditions = []
        rates = []
        exceptions = []

        # 1. Extract Conclusion section
        m_concl = re.search(r"KẾT LUẬN\s*:\s*(.*?)(?=\n-|\n[A-ZÀ-Ỹ\s]+:|$)", raw_text, re.DOTALL | re.IGNORECASE)
        if m_concl:
            conclusion = m_concl.group(1).strip()
        else:
            first_lines = [l.strip() for l in raw_text.split("\n") if l.strip() and not l.startswith("#")]
            conclusion = first_lines[0] if first_lines else raw_text[:200]

        # 2. Extract Conditions / Rates / Exceptions
        m_cond = re.search(r"ĐIỀU KIỆN\s*(?:VÀ MỨC ÁP DỤNG)?\s*:\s*(.*?)(?=\n-|\n[A-ZÀ-Ỹ\s]+:|$)", raw_text, re.DOTALL | re.IGNORECASE)
        if m_cond:
            for line in m_cond.group(1).strip().split("\n"):
                clean = re.sub(r"^[\*\-\+\d\.\)]\s*", "", line).strip()
                if clean:
                    conditions.append(clean)

        m_note = re.search(r"LƯU Ý\s*(?:/NGOẠI LỆ)?\s*:\s*(.*?)(?=\n-|\n[A-ZÀ-Ỹ\s]+:|$)", raw_text, re.DOTALL | re.IGNORECASE)
        if m_note:
            for line in m_note.group(1).strip().split("\n"):
                clean = re.sub(r"^[\*\-\+\d\.\)]\s*", "", line).strip()
                if clean and "không có" not in clean.lower():
                    exceptions.append(clean)

        # 3. Extract percentages and time limits
        all_percentages = re.findall(r"\b\d+(?:[.,]\d+)?%", raw_text)
        all_durations = re.findall(r"\b\d+\s+(?:ngày|tháng|năm|giờ)\b", raw_text, re.IGNORECASE)
        rates = list(dict.fromkeys(all_percentages + all_durations))

        # 4. Strict Citation Grounding: Match Articles and Clauses mentioned against retrieved chunks
        citations: List[LegalCitation] = []
        for c in chunks:
            art_num_match = re.search(r"Điều\s+(\d+)", c.article)
            if art_num_match:
                art_pattern = r"\bĐiều\s+" + art_num_match.group(1) + r"\b"
                if re.search(art_pattern, raw_text, re.IGNORECASE):
                    # Check if clause is also mentioned
                    cl_match = re.search(r"Khoản\s+(\d+)", c.clause)
                    cl_mentioned = False
                    if cl_match:
                        cl_pattern = r"\bkhoản\s+" + cl_match.group(1) + r"\b"
                        if re.search(cl_pattern, raw_text, re.IGNORECASE):
                            cl_mentioned = True

                    citations.append(LegalCitation(
                        document_name=c.document_name,
                        document_number=c.document_number,
                        article=c.article,
                        clause=c.clause,
                        page_start=c.page_start,
                        chunk_id=c.chunk_id
                    ))

        # Default fallback to top chunk if no specific article mentioned
        if not citations and chunks:
            for c in chunks[:2]:
                citations.append(LegalCitation(
                    document_name=c.document_name,
                    document_number=c.document_number,
                    article=c.article,
                    clause=c.clause,
                    page_start=c.page_start,
                    chunk_id=c.chunk_id
                ))

        # Deduplicate citations
        unique_citations = []
        seen = set()
        for cit in citations:
            key = (cit.document_number, cit.article, cit.clause)
            if key not in seen:
                seen.add(key)
                unique_citations.append(cit)

        # 5. Compile Fact-to-Law metadata
        ext_facts = []
        leg_issues = []
        miss_facts = []
        if fact_profile:
            ext_facts = [f"Chủ thể: {', '.join(fact_profile.subjects)}"]
            if fact_profile.actions:
                ext_facts.append(f"Sự kiện: {', '.join(fact_profile.actions)}")
            if fact_profile.numbers_and_durations:
                ext_facts.append(f"Dữ kiện số: {', '.join(fact_profile.numbers_and_durations)}")
            leg_issues = fact_profile.legal_issues
            miss_facts = fact_profile.missing_facts

        return LegalAnalysisResult(
            status=status,
            is_sufficient=is_sufficient,
            conclusion=conclusion,
            legal_citations=unique_citations,
            conditions=conditions,
            rates_and_deadlines=rates,
            exceptions=exceptions,
            extracted_facts=ext_facts,
            legal_issues=leg_issues,
            missing_facts=miss_facts,
            temporal_notes=temporal_notes or [],
            raw_llm_response=raw_text,
            inference_time_sec=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
