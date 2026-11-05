import sys
import time
import argparse
from pathlib import Path

# Fix terminal encoding on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.orchestrator import LegalAgentOrchestrator, ChatbotResult

def print_banner():
    banner = """
========================================================================================
       VIETNAMESE AGENTIC LEGAL CHATBOT - MULTI-TURN CONVERSATION MEMORY
       Bộ luật Lao động (18/VBHN-VPQH) & Luật Bảo hiểm xã hội (41/2024/QH15)
========================================================================================
    """
    print(banner)

def display_result(result: ChatbotResult):
    print("\n" + "="*88)
    print(f"CÂU HỎI GỐC: {result.question}")
    print(f"SESSION ID:  {result.session_id}")
    print("="*88)

    # 0. MEMORY & REWRITER
    print("\n[BƯỚC 0: CONVERSATION MEMORY & QUERY REWRITER]")
    print(f"  * Câu hỏi tiếp nối (Follow-up): {result.is_follow_up}")
    if result.is_rewritten:
        print(f"  * [ĐÃ VIẾT LẠI]:               {result.rewritten_query}")
    else:
        print(f"  * Trạng thái viết lại:          Giữ nguyên câu hỏi độc lập")
    if result.conversation_state:
        topic = result.conversation_state.get("current_topic")
        facts = result.conversation_state.get("user_provided_facts", {})
        print(f"  * Chủ đề tích lũy:             {topic}")
        if facts:
            print(f"  * Dữ kiện tích lũy:            {facts}")
    print(f"  * Thời gian phân tích & xử lý: {result.timing.rewriting_time * 1000:.2f} ms")

    # If Clarification is needed, display and return
    if not result.response.is_answerable and "LÀM RÕ" in result.response.formatted_markdown:
        print("\n" + "-"*88)
        print("[YÊU CẦU LÀM RÕ THÔNG TIN]")
        print(result.response.formatted_markdown)
        print("="*88)
        return

    # 1. INTENT AGENT
    print("\n[BƯỚC 1: INTENT AGENT]")
    print(f"  * Lĩnh vực (Domain):       {result.intent.domain.upper()}")
    print(f"  * Trong phạm vi (InScope): {result.intent.is_in_scope}")
    print(f"  * Độ tin cậy (Confidence): {result.intent.confidence * 100:.1f}%")
    print(f"  * Câu hỏi chuẩn hóa:       {result.intent.normalized_query}")
    print(f"  * Câu hỏi mở rộng từ khóa: {result.intent.expanded_query}")
    print(f"  * Giải thích:              {result.intent.explanation}")
    print(f"  * Thời gian xử lý:         {result.timing.intent_time * 1000:.1f} ms")

    # If Out of Scope, show response and exit
    if not result.intent.is_in_scope:
        print("\n" + "-"*88)
        print("[KẾT QUẢ CUỐI CÙNG (NGOÀI PHẠM VI)]")
        print(result.response.formatted_markdown)
        print(f"Tổng thời gian: {result.timing.total_time:.2f}s | RAM: {result.resources.process_ram_after_mb:.1f} MB")
        print("="*88)
        return

    # 2. RETRIEVAL AGENT
    ret = result.retrieval
    if ret:
        print("\n[BƯỚC 2: RETRIEVAL AGENT (Hybrid Search + Parent-Child Expansion)]")
        print(f"  * Tổng số chunks thu thập: {ret.total_retrieved} (Primary: {len(ret.primary_chunks)}, Expanded: {len(ret.expanded_chunks)})")
        print(f"  * Các Điều luật liên quan:  {', '.join(ret.unique_articles[:5])}")
        print(f"  * Thời gian xử lý:         {result.timing.retrieval_time:.2f} s")
        print("  * Danh sách Top Chunks được cung cấp cho LLM:")
        for idx, c in enumerate(ret.all_chunks[:6], 1):
            ext_tag = "[Parent-Child]" if c.is_parent_child_expanded else f"[Rank {c.retrieval_rank}]"
            print(f"     ({idx}) {ext_tag:15} {c.document_name} | {c.article} | {c.clause} (Trang {c.page_start})")
            snippet = c.text.replace("\n", " ").strip()[:110]
            print(f"         Trích đoạn: {snippet}...")

    # 3. LEGAL ANALYSIS AGENT
    ana = result.analysis
    if ana:
        print("\n[BƯỚC 3: LEGAL ANALYSIS AGENT (Local LLM Qwen2.5-1.5B Q4_K_M)]")
        print(f"  * Trạng thái phân tích:    {ana.status.upper()} (Đủ căn cứ: {ana.is_sufficient})")
        print(f"  * Tokens sinh ra:          {ana.completion_tokens} tokens")
        print(f"  * Thời gian suy luận:      {result.timing.analysis_time:.2f} s")
        print(f"  * Căn cứ trích xuất:       {[f'{c.article} {c.clause}' for c in ana.legal_citations]}")
        if ana.rates_and_deadlines:
            print(f"  * Tỷ lệ/Thời hạn trích xuất: {', '.join(ana.rates_and_deadlines)}")

    # 4. VALIDATION AGENT
    val = result.validation
    if val:
        print("\n[BƯỚC 4: VALIDATION AGENT (Kiểm định độc lập qua Python Rules)]")
        print(f"  * Trạng thái kiểm định:    {val.validation_status} (Hợp lệ: {val.is_valid})")
        print(f"  * Số kiểm tra đã vượt qua: {len(val.passed_checks)}")
        for pc in val.passed_checks[:4]:
            print(f"     [PASS] {pc}")
        if val.warning_messages:
            for wm in val.warning_messages:
                print(f"     [WARN] {wm}")
        if val.error_messages:
            for em in val.error_messages:
                print(f"     [FAIL] {em}")
        print(f"  * Thời gian kiểm định:     {result.timing.validation_time * 1000:.1f} ms")

    # 5. RESPONSE AGENT
    print("\n" + "="*88)
    print("[BƯỚC 5: CÂU TRẢ LỜI TƯ VẤN CUỐI CÙNG (RESPONSE AGENT)]")
    print("="*88)
    print(result.response.formatted_markdown)

    # 6. PERFORMANCE & RESOURCES
    print("\n" + "-"*88)
    print("[THỐNG KÊ HIỆU NĂNG VÀ TÀI NGUYÊN HỆ THỐNG]")
    print(f"  * Rewriting Step:   {result.timing.rewriting_time * 1000:6.2f} ms")
    print(f"  * Intent Agent:     {result.timing.intent_time * 1000:6.1f} ms")
    print(f"  * Retrieval Agent:  {result.timing.retrieval_time:6.2f} s")
    print(f"  * Analysis Agent:   {result.timing.analysis_time:6.2f} s")
    print(f"  * Validation Agent: {result.timing.validation_time * 1000:6.1f} ms")
    print(f"  * Response Agent:   {result.timing.response_time * 1000:6.1f} ms")
    print(f"  -------------------------------------------")
    print(f"  * TỔNG THỜI GIAN:   {result.timing.total_time:6.2f} s (Số lần Retry: {result.retries_count})")
    print(f"  * RAM Tiến trình:   {result.resources.process_ram_before_mb:.1f} MB -> {result.resources.process_ram_after_mb:.1f} MB (Delta: {result.resources.process_ram_delta_mb:+.1f} MB)")
    print(f"  * RAM Hệ thống:     {result.resources.system_ram_used_gb:.2f} GB / {result.resources.system_ram_total_gb:.2f} GB (Chiếm {result.resources.system_ram_percent}%)")
    print("="*88 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Vietnamese Agentic Legal Chatbot - Multi-turn CLI")
    parser.add_argument("--query", "-q", type=str, help="Câu hỏi tư vấn pháp lý cần kiểm tra")
    parser.add_argument("--interactive", "-i", action="store_true", help="Chạy chế độ tương tác nhập câu hỏi liên tục theo session")
    args = parser.parse_args()

    print_banner()
    orchestrator = LegalAgentOrchestrator()

    if args.query:
        result = orchestrator.process_query(args.query)
        display_result(result)
        return

    if args.interactive:
        session_id = f"cli_{int(time.time())}"
        print(f"\nChế độ hội thoại liên tục (Multi-turn). Session ID: {session_id}")
        print("Mẹo: Gõ '/new' hoặc '/reset' để mở phiên mới. Gõ 'exit' hoặc 'quit' để thoát.\n")
        while True:
            try:
                user_q = input("\n[Bạn hỏi]: ").strip()
                if not user_q:
                    continue
                if user_q.lower() in ["exit", "quit", "thoát"]:
                    print("Tạm biệt!")
                    break
                if user_q.lower() in ["/new", "/reset", "xóa ngữ cảnh", "cuộc trò chuyện mới"]:
                    orchestrator.session_manager.clear_session(session_id)
                    session_id = f"cli_{int(time.time())}"
                    print(f"-> Đã khởi tạo phiên mới: {session_id}\n")
                    continue

                result = orchestrator.process_query(user_q, session_id=session_id)
                display_result(result)
            except KeyboardInterrupt:
                print("\nKết thúc phiên làm việc.")
                break
    else:
        sample_q = "Lương làm thêm cuối tuần là bao nhiêu?"
        print(f"Chạy kiểm tra mặc định với câu hỏi mẫu (MT01 Turn 1):\n\"{sample_q}\"\n")
        result = orchestrator.process_query(sample_q)
        display_result(result)

if __name__ == "__main__":
    main()
