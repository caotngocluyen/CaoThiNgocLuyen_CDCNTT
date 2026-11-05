import sys
import time
from pathlib import Path
import streamlit as st

# Configure encoding
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.orchestrator import LegalAgentOrchestrator, ChatbotResult

st.set_page_config(
    page_title="Tư Vấn Pháp Luật Lao Động & BHXH",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom minimalist styling
st.markdown("""
<style>
    .main-title {
        font-size: 1.85rem;
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 1.25rem;
    }
    .sidebar-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sidebar-caption {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_orchestrator():
    return LegalAgentOrchestrator()

# Initialize Orchestrator
with st.spinner("Đang khởi tạo hệ thống..."):
    orchestrator = load_orchestrator()

# Ensure session_id exists in session state
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time()*1000)}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: clean session controls and suggested questions
with st.sidebar:
    st.markdown('<div class="sidebar-title">Tư Vấn Pháp Luật</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">Bộ luật Lao động & Luật Bảo hiểm xã hội</div>', unsafe_allow_html=True)

    if st.button("Cuộc trò chuyện mới", use_container_width=True):
        orchestrator.session_manager.clear_session(st.session_state.session_id)
        st.session_state.session_id = f"session_{int(time.time()*1000)}"
        st.session_state.messages = []
        st.rerun()

    active_mem = orchestrator.session_manager.get_or_create_memory(st.session_state.session_id)
    if active_mem.state.current_topic_label:
        st.markdown(f"**Chủ đề hiện tại:** {active_mem.state.current_topic_label}")
    if active_mem.state.user_provided_facts:
        st.markdown("**Dữ kiện đã ghi nhận:**")
        for k, v in active_mem.state.user_provided_facts.items():
            st.write(f"- {k}: {v}")

    st.markdown("---")
    st.subheader("Câu hỏi gợi ý")
    sample_queries = [
        "Lương làm thêm cuối tuần là bao nhiêu?",
        "Lương của tôi là 30 triệu thì sao?",
        "Người lao động được nghỉ phép năm bao nhiêu ngày?",
        "Nếu làm việc 5 năm thì sao?",
        "Điều kiện hưởng chế độ thai sản là gì?",
        "Vậy cần đóng bảo hiểm bao lâu?",
        "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
    ]

    selected_sample = None
    for q in sample_queries:
        if st.button(q, key=f"btn_{hash(q)}", use_container_width=True):
            selected_sample = q

# Main UI Header
st.markdown('<div class="main-title">Tư Vấn Pháp Luật Lao Động & BHXH</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống giải đáp pháp luật tự động dựa trên căn cứ Điều, Khoản quy định hiện hành.</div>', unsafe_allow_html=True)

# Input query
user_query = st.chat_input("Nhập câu hỏi pháp lý cần tư vấn...")
if selected_sample:
    user_query = selected_sample

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.spinner("Đang xử lý câu hỏi..."):
        result: ChatbotResult = orchestrator.process_query(
            user_question=user_query,
            session_id=st.session_state.session_id
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.response.formatted_markdown,
            "result": result
        })

# Render conversation
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

            res: ChatbotResult = msg.get("result")
            if res and res.retrieval and res.retrieval.unique_articles:
                with st.expander("Căn cứ tra cứu và kiểm định", expanded=False):
                    st.markdown(f"**Điều khoản áp dụng:** {', '.join(res.retrieval.unique_articles)}")
                    if res.validation:
                        status = res.validation.validation_status
                        status_label = "Đạt yêu cầu" if status == "PASSED" else ("Cần lưu ý" if status == "WARNING" else "Chưa đạt")
                        st.markdown(f"**Kết quả kiểm định:** {status_label}")
                        if res.validation.passed_checks:
                            for chk in res.validation.passed_checks:
                                st.write(f"- [Đạt] {chk}")
                        if res.validation.warning_messages:
                            for w in res.validation.warning_messages:
                                st.write(f"- [Lưu ý] {w}")
                        if res.validation.error_messages:
                            for e in res.validation.error_messages:
                                st.write(f"- [Chưa đạt] {e}")
