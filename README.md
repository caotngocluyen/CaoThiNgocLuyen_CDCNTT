# AGENTIC AI LEGAL CHATBOT (PHÁP LUẬT LAO ĐỘNG & BẢO HIỂM XÃ HỘI VIỆT NAM)

Hệ thống Trợ lý Pháp lý Thông minh Đa tác tử (Agentic AI Multi-Agent) hỗ trợ tra cứu, phân tích và tư vấn quy định pháp luật lao động và bảo hiểm xã hội Việt Nam. Hệ thống được tối ưu hóa để vận hành **100% CỤC BỘ (Offline Local CPU)** trên phần cứng máy tính cá nhân 16 GB RAM, không phụ thuộc và không gọi bất kỳ dịch vụ API LLM đám mây nào bên ngoài.

---

## 1. TỔNG QUAN KIẾN TRÚC MULTI-AGENT & MULTI-TURN CONVERSATION MEMORY

Hệ thống áp dụng mô hình điều phối tập trung với 5 Agent chuyên biệt hóa:

```
[Người dùng] ---> [IntentAgent] ---> [RetrievalAgent] (BM25 + Dense + Parent-Child)
                        |                      |
                        | (Early Exit OOS)     v
                        |              [LegalAnalysisAgent] (Qwen2.5-1.5B GGUF Q4_K_M)
                        |                      |
                        |                      v
                        |              [ValidationAgent] (Python Deterministic)
                        |                      |
                        v                      v
                 [ResponseAgent] <--- (Retry nếu thiếu căn cứ)
                        |
                        v
                [Giao diện Chatbot Streamlit]
```

0. **Conversation Memory & Query Rewriting (`src/memory/`):**
   - **ConversationMemory (`src/memory/conversation_memory.py`):** Quản lý lịch sử và trạng thái hội thoại (`ConversationState`), lưu vết chủ đề (`current_topic`), Điều luật liên quan, và dữ kiện người dùng (mức lương, thâm niên). Giới hạn cửa sổ trượt (`max_turns=6`) chống tràn context LLM.
   - **SessionManager:** Quản lý phiên độc lập, đảm bảo cô lập dữ liệu tuyệt đối giữa các session người dùng.
   - **Context-Aware Query Rewriter (`src/memory/query_rewriter.py`):** Phân tích câu hỏi tiếp nối, viết lại câu hỏi ngắn/tỉnh lược thành truy vấn pháp lý hoàn chỉnh trước khi chuyển đến Retrieval; nhận diện chuyển chủ đề (topic shift) để làm sạch dữ kiện cũ; phát hiện câu hỏi mơ hồ để yêu cầu làm rõ.
1. **IntentAgent (`src/agents/intent_agent.py`):**
   - Phân loại miền câu hỏi: `labor_law`, `social_insurance`, `mixed`, hoặc `out_of_scope`.
   - Chuẩn hóa ngữ nghĩa tiếng Việt và tự động mở rộng từ khóa tương đương (Synonym Query Expansion).
   - Kích hoạt cơ chế **Early Exit** khi gặp câu hỏi ngoài phạm vi trong < 2ms, tiết kiệm 100% tài nguyên CPU.
2. **RetrievalAgent (`src/agents/retrieval_agent.py`):**
   - Phối hợp tìm kiếm lai (Hybrid Search): BM25 (sparse) + ChromaDB (dense cosine) với mô hình cục bộ `sentence-transformers/all-MiniLM-L6-v2`.
   - Kết hợp xếp hạng bằng thuật toán Reciprocal Rank Fusion (RRF, $k=60$).
   - Cơ chế **Parent-Child Context Expansion**: Tự động mở rộng các Khoản anh em trong cùng Điều luật khi tìm thấy ít nhất 1 Khoản liên quan, bảo toàn ngữ cảnh điều luật phức tạp.
3. **LegalAnalysisAgent (`src/agents/legal_analysis_agent.py`):**
   - Sử dụng Local LLM **Qwen2.5-1.5B-Instruct GGUF Q4_K_M** thông qua `llama-cpp-python` (6 threads CPU, context 3072).
   - Trích xuất căn cứ pháp lý, điều kiện áp dụng, tỷ lệ (%), thời hạn và ngoại lệ.
   - Nguyên tắc nghiêm ngặt: Nếu không đủ căn cứ, bắt buộc gắn cờ `is_sufficient=False` để Orchestrator xử lý, tuyệt đối không suy diễn.
4. **ValidationAgent (`src/agents/validation_agent.py`):**
   - Kiểm định độc lập bằng Python thuần (Deterministic), không dùng LLM để chống ảo giác kiểm định.
   - Đối chiếu trực tiếp với 1.296 chunks gốc: kiểm tra tính tồn tại của `chunk_id`, số hiệu văn bản, Điều, Khoản, và trang nguồn.
   - **Strict Clause-Level Grounding:** Phân tách 3 vùng ngữ cảnh (`strict_cited_corpus`, `parent_art_corpus`, `global_corpus`). Chặn đứng trường hợp số liệu xuất hiện ở Khoản anh em mà lại cho PASSED tự động.
   - **Tiered Condition-Rate Consistency:** Kiểm tra xung đột logic giữa điều kiện áp dụng và tỷ lệ (ví dụ: bắt lỗi nếu gán mức 65% với điều kiện "dưới 15 năm").
5. **ResponseAgent (`src/agents/response_agent.py`):**
   - Chuẩn hóa văn bản trả lời theo cấu trúc 4 phần pháp lý chuyên nghiệp:
     1. KẾT LUẬN TRỰC TIẾP
     2. CĂN CỨ PHÁP LÝ (Văn bản, Điều, Khoản, Ngày hiệu lực, Ngày xác thực VBHN)
     3. QUY ĐỊNH CHI TIẾT & ĐIỀU KIỆN ÁP DỤNG
     4. LƯU Ý PHÁP LÝ & GIỚI HẠN DỮ LIỆU

---

## 2. DỮ LIỆU PHÁP LUẬT ĐÃ TÍCH HỢP

Cơ sở dữ liệu Knowledge Base (`data/processed/legal_chunks.json` - 1.296 chunks):
1. **Bộ luật Lao động:**
   - Văn bản gốc: **Bộ luật Lao động số 45/2019/QH14** (Quốc hội khóa XIV thông qua ngày 20/11/2019, có hiệu lực từ ngày **01/01/2021**).
   - Văn bản hợp nhất: Số **18/VBHN-VPQH** do Văn phòng Quốc hội ban hành và xác thực ngày **12/02/2026** (ký bởi Chủ nhiệm VPQH Lê Quang Mạnh).
2. **Luật Bảo hiểm xã hội:**
   - Văn bản pháp luật: **Luật Bảo hiểm xã hội số 41/2024/QH15** (Quốc hội khóa XV thông qua ngày 29/06/2024, có hiệu lực từ ngày **01/07/2025**).

---

## 3. YÊU CẦU HỆ THỐNG VÀ CÀI ĐẶT

### 3.1. Yêu cầu phần cứng
- **Hệ điều hành:** Windows 10/11, Linux hoặc macOS.
- **CPU:** Tối thiểu 4 cores (khuyến nghị 6 - 12 logical cores).
- **RAM:** Tối thiểu 16 GB vật lý (tiến trình Python Chatbot chiếm dụng đỉnh ~2.36 GB RSS).
- **Ổ cứng:** Còn trống tối thiểu 5 GB (mô hình LLM GGUF chiếm 1.04 GB).

### 3.2. Cài đặt môi trường
Yêu cầu Python 3.10 hoặc 3.11:

```bash
# 1. Kích hoạt môi trường ảo (nếu có)
python -m venv venv
venv\Scripts\activate

# 2. Cài đặt các thư viện cần thiết
pip install llama-cpp-python sentence-transformers chromadb rank-bm25 psutil streamlit
```

---

## 4. HƯỚNG DẪN CHẠY ỨNG DỤNG

### 4.1. Khởi động Giao diện Web Streamlit
Chạy lệnh sau từ thư mục gốc dự án:

```bash
streamlit run app.py
```
Sau khi khởi động, mở trình duyệt tại địa chỉ mặc định: `http://localhost:8501`.
Giao diện cung cấp:
- Hộp thoại hỏi đáp tư vấn pháp lý trực quan.
- Sidebar hiển thị trạng thái tài nguyên thời gian thực (Process RAM, System RAM, CPU threads).
- Tabs chẩn đoán kỹ thuật: Inspect Intent, Retrieval Chunks, Parent-Child Expansion, và Validation Trace.

### 4.2. Chạy Kiểm thử Toàn trình & Đo lường Tài nguyên qua CLI
```bash
# Kiểm thử đơn vị Bộ nhớ hội thoại & Động cơ viết lại truy vấn:
python tests/test_conversation_memory.py

# Kiểm thử 10 kịch bản Hội thoại Đa lượt (Multi-turn MT01 -> MT10):
python tests/test_multi_turn_conversation.py

# Chạy kiểm thử hồi quy cấp Khoản cho Điều 45 Luật BHXH:
python tests/test_validation_clause_level.py

# Chạy kiểm toán đối sánh truy xuất 3 giai đoạn:
python tests/audit_stage1_retrieval_comparison.py

# Chạy bộ kịch bản kiểm thử Multi-Agent toàn diện:
python tests/audit_stage3_multi_agent_suite.py

# Đo lường chi tiết RAM và độ trễ (Median & P95):
python tests/benchmark_ram_latency.py
```

---

## 5. KỊCH BẢN DEMO TÁI LẬP (REPRODUCIBLE DEMO SCENARIOS)

| Kịch bản | Câu hỏi kiểm thử mẫu | Lĩnh vực | Căn cứ pháp lý kỳ vọng | Kết quả xử lý của Chatbot |
| :--- | :--- | :---: | :---: | :--- |
| **Demo 1 (Lao động)** | *"Thời gian thử việc tối đa đối với người làm công việc cần trình độ đại học trở lên là bao nhiêu ngày?"* | `labor_law` | Điều 25 Khoản 2 BLLĐ 2019 (18/VBHN-VPQH) | Trả lời chính xác: Tối đa **60 ngày**. Validation: `PASSED`. |
| **Demo 2 (BHXH)** | *"Mức hưởng chế độ ốm đau thông thường của người lao động bằng bao nhiêu phần trăm tiền lương?"* | `social_insurance` | Điều 45 Khoản 2 Luật BHXH 2024 (41/2024/QH15) | Trả lời chính xác: **75%** tiền lương đóng BHXH của tháng liền kề. |
| **Demo 3 (Đa ý)** | *"Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng lao động trong những trường hợp nào và phải báo trước bao nhiêu ngày?"* | `labor_law` | Điều 36 BLLĐ 2019 | Liệt kê các trường hợp và phân định chính xác thời hạn: **45 ngày** (HĐLĐ không thời hạn), **30 ngày** (HĐLĐ từ 12-36 tháng), **03 ngày làm việc** (HĐLĐ dưới 12 tháng). |
| **Demo 4 (Thiếu dữ liệu)** | *"Nghỉ việc được hưởng tiền gì?"* | `labor_law` | Điều 46, Điều 113 BLLĐ 2019 | Liệt kê trợ cấp thôi việc, tiền phép năm chưa nghỉ; cảnh báo rõ: Bảo hiểm thất nghiệp thuộc Luật Việc làm hiện chưa nằm trong KB. |
| **Demo 5 (Ngoài phạm vi)** | *"Thời hạn chuyển nhượng đất nông nghiệp theo Luật Đất đai là bao nhiêu năm?"* | `out_of_scope` | Không | Early-exit trong 0.00 ms, từ chối lịch sự và tiết kiệm 100% CPU. |
| **Demo 6 (Chống Bịa đặt)** | *"Theo Luật Hàng không dân dụng, hủy chuyến bay được bồi thường bao nhiêu tiền?"* | Ngoại miền | Không | ValidationAgent phát hiện và chặn đứng hallucination tỷ lệ bịa đặt (đánh dấu `FAILED`). |
| **Demo 7 (Gây nhiễu)** | *"Hợp đồng thử việc bảo hiểm xã hội tính bao nhiêu phần trăm lương làm thêm giờ?"* | `mixed` | Điều 24, 98 BLLĐ 2019 & Điều 2 Luật BHXH 2024 | Phân tích tách bạch: Hợp đồng thử việc riêng không đóng BHXH bắt buộc; thỏa thuận thử việc trong HĐLĐ đóng BHXH; lương làm thêm giờ tính riêng theo Điều 98. |

---

## 6. HẠN CHẾ ĐÃ BIẾT VÀ HƯỚNG PHÁT TRIỂN (KNOWN LIMITATIONS)

1. **Phạm vi văn bản:** Hiện Knowledge Base tập trung vào 2 văn bản trụ cột là Bộ luật Lao động 2019 (VBHN 18/VBHN-VPQH) và Luật Bảo hiểm xã hội 2024 (41/2024/QH15). Các chế định về Bảo hiểm thất nghiệp (Luật Việc làm 2013) và các Nghị định hướng dẫn chi tiết (NĐ 145/2020/NĐ-CP, NĐ 12/2022/NĐ-CP) cần được số hóa bổ sung ở giai đoạn tiếp theo.
2. **Tốc độ suy luận CPU:** Do chạy mô hình ngôn ngữ cục bộ hoàn toàn trên CPU máy tính cá nhân không có card đồ họa GPU rời, thời gian sinh văn bản trung bình dao động từ 12 - 18 giây/câu hỏi.

---

## 7. BẢN QUYỀN VÀ BẢO MẬT
- **Bảo mật tuyệt đối:** Mã nguồn không chứa bất kỳ secret key, API token hay thông tin định danh nhạy cảm nào.
- **Vận hành Offline:** Hệ thống ngắt kết nối mạng Internet vẫn hoạt động bình thường 100%.
