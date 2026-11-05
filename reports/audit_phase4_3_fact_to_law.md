# BÁO CÁO KIỂM TOÁN VÀ NGHIỆM THU PHASE 4.3: TÁI CẤU TRÚC FACT-TO-LAW REASONING
**HỆ THỐNG AGENTIC AI LEGAL CHATBOT (PHÁP LUẬT LAO ĐỘNG & BẢO HIỂM XÃ HỘI VIỆT NAM)**

*Thời gian nghiệm thu:* 04/11/2026  
*Môi trường thực thi:* Windows 11, CPU Intel Core i5, RAM 16 GB, 100% Cục bộ / Offline, không GPU.  
*Mô hình suy luận:* Local LLM `Qwen2.5-1.5B-Instruct` GGUF (Q4_K_M) qua `llama-cpp-python`.  
*Tệp bằng chứng đo đạc:* `reports/audit_phase4_3_fact_to_law.json` và `tests/test_results_phase3.json`.

---

## 1. HIỆN TRẠNG LEGALANALYSISAGENT TRƯỚC KHI SỬA

Trước Phase 4.3, [src/agents/legal_analysis_agent.py](file:///d:/A_DATN/Agentic_Legal_Chatbot/src/agents/legal_analysis_agent.py) hoạt động theo cơ chế Single-shot Prompting đơn giản:
- **Ngữ cảnh (Context):** Gom 6 chunk đầu tiên từ `RetrievalContext` thành một chuỗi văn bản phẳng.
- **Prompt:** Yêu cầu mô hình trả lời theo 4 đầu mục: `KẾT LUẬN`, `CĂN CỨ PHÁP LÝ`, `ĐIỀU KIỆN VÀ MỨC ÁP DỤNG`, `LƯU Ý/NGOẠI LỆ`.
- **Parser:** Dùng regex đơn giản để bóc tách các dòng tương ứng và tìm số Điều/Khoản trong văn bản.

---

## 2. NHỮNG VẤN ĐỀ KỸ THUẬT PHÁT HIỆN

Qua kiểm tra đối soát thực tế và phân tích hành vi của mô hình nhỏ 1.5B trên CPU, các hạn chế kỹ thuật lớn được xác định:

1. **Thiếu bước bóc tách dữ kiện (Fact Extraction):**  
   Mô hình đọc câu hỏi và cố gắng đưa ra kết luận ngay mà không phân lập chủ thể (người lao động, người sử dụng lao động), hành vi (thử việc, nghỉ việc, ốm đau) và các số liệu thời hạn (2 tháng, 60 ngày, 12 tháng).
2. **Bỏ sót ngoại lệ và điều kiện loại trừ (Exception Blindspot):**  
   Nhiều điều luật của Việt Nam có cấu trúc *"được thực hiện... trừ trường hợp quy định tại..."* (ví dụ Điều 35 Khoản 2 BLLĐ 2019 loại trừ Điều 29). Mô hình 1.5B thường chỉ nắm vế đầu mà bỏ qua điều kiện ngoại lệ.
3. **Mù mờ về thời điểm hiệu lực pháp luật (Temporal Blindspot):**  
   Hệ thống có 2 văn bản: Bộ luật Lao động (hiệu lực 01/01/2021) và Luật BHXH 2024 (hiệu lực 01/07/2025). Trước Phase 4.3, mô hình không được báo hiệu về mốc 01/07/2025, dẫn đến việc khẳng định luật mới áp dụng cho cả các sự kiện đang diễn ra ở thời điểm hiện tại.
4. **Không phát hiện được dữ kiện còn thiếu (Missing Facts):**  
   Khi người dùng hỏi chung chung (ví dụ: *"Thử việc có phải đóng BHXH không?"*), hệ thống thường khẳng định một chiều (không đóng) mà không chỉ ra điều kiện phân nhánh quan trọng: nếu thỏa thuận thử việc ghi trong HĐLĐ từ 1 tháng trở lên thì vẫn phải đóng BHXH bắt buộc theo Luật BHXH.
5. **Nguy cơ phình to Token và tăng độ trễ:**  
   Nếu không có cấu trúc hướng dẫn súc tích, mô hình có xu hướng chép lại nguyên văn nhiều đoạn luật không liên quan, khiến độ trễ trên CPU kéo dài trên 35-50 giây.

---

## 3. THIẾT KẾ MỚI: QUY TRÌNH FACT-TO-LAW SYLLOGISM

Kiến trúc Phase 4.3 triển khai quy trình Tam đoạn luận pháp lý 6 bước kết hợp **Rule-based Pre-extraction (Python thuần < 1 ms)** và **Syllogistic LLM Generation (1 call duy nhất trên CPU)**:

```
[Câu hỏi người dùng]
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bước 1: Fact & Issue Pre-Extractor (Pure Python Regex < 1 ms)   │
│ - Trích xuất Chủ thể (actor), Hành vi (action), Dữ kiện số       │
│ - Nhận diện Vấn đề pháp lý (Issues): Điều kiện / Mức / Thời hạn │
│ - Phát hiện Dữ kiện còn thiếu (Missing Facts Checklist)         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bước 2: Syllogistic Prompt Builder                              │
│ - Đính kèm Mốc thời gian hiệu lực (Temporal Metadata)           │
│ - Ép cấu trúc Tam đoạn luận: Tiền đề quy phạm -> Đối chiếu thực tế │
│ - Khống chế độ dài súc tích (ngăn ngừa chép lan man)             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bước 3: Single-Call Local LLM Inference (Qwen2.5-1.5B CPU)      │
│ Sinh có định hướng:                                             │
│ 1. DỮ KIỆN VÀ VẤN ĐỀ                                            │
│ 2. CĂN CỨ VÀ QUY TẮC PHÁP LÝ (Major Premise)                    │
│ 3. ĐỐI CHIẾU THỰC TẾ (Subsumption)                              │
│ 4. KẾT LUẬN PHÁP LÝ (Conclusion)                                │
│ 5. HIỆU LỰC VÀ LƯU Ý NGOẠI LỆ (Exceptions & Validity)           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bước 4: Fact-to-Law Response Parser & Evidence Mapping          │
│ - Bóc tách cấu trúc 5 phần                                      │
│ - Strict Citation Mapping: Liên kết trực tiếp từng điều trích   │
│   dẫn với chunk_id, số trang trong Knowledge Base               │
│ - Tích hợp đầy đủ vào ValidationAgent và ResponseAgent          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. DANH MỤC CÁC FILE ĐÃ TẠO VÀ CHỈNH SỬA

1. **Tạo mới:** [src/agents/fact_reasoning.py](file:///d:/A_DATN/Agentic_Legal_Chatbot/src/agents/fact_reasoning.py)
   - Lớp `FactExtractor`: Bóc tách chủ thể, hành vi, dữ kiện số, vấn đề pháp lý và phát hiện dữ kiện còn thiếu.
   - Lớp `FactToLawPromptBuilder`: Xây dựng prompt tam đoạn luận kèm mốc thời gian hiệu lực văn bản.
2. **Cập nhật:** [src/agents/legal_analysis_agent.py](file:///d:/A_DATN/Agentic_Legal_Chatbot/src/agents/legal_analysis_agent.py)
   - Bổ sung các trường dữ liệu mới vào `LegalAnalysisResult`: `extracted_facts`, `legal_issues`, `missing_facts`, `temporal_notes`.
   - Nâng cấp phương thức `analyze()` và `_parse_llm_response()` để thực thi quy trình Fact-to-Law.
3. **Tạo mới:** [tests/test_fact_to_law_evaluation.py](file:///d:/A_DATN/Agentic_Legal_Chatbot/tests/test_fact_to_law_evaluation.py)
   - Bộ kiểm chuẩn 5 kịch bản chuyên sâu về dữ kiện, ngoại lệ, hiệu lực và thiếu thông tin.
4. **Tạo mới:** [reports/audit_phase4_3_fact_to_law.json](file:///d:/A_DATN/Agentic_Legal_Chatbot/reports/audit_phase4_3_fact_to_law.json)
   - Dữ liệu đo đạc thực nghiệm chi tiết từng kịch bản.

---

## 5. KẾT QUẢ ĐÁNH GIÁ THỰC NGHIỆM TRÊN 5 KỊCH BẢN NÂNG CAO

Thử nghiệm độc lập được thực thi trên môi trường cách ly phiên (Session Isolation), kết quả trích xuất trực tiếp từ [reports/audit_phase4_3_fact_to_law.json](file:///d:/A_DATN/Agentic_Legal_Chatbot/reports/audit_phase4_3_fact_to_law.json):

| Mã Test | Kịch bản kiểm thử | Fact Extraction | Legal Issue | Rule Matching | Ngoại lệ & Điều kiện | Dữ kiện còn thiếu | Hiệu lực thời gian | Trạng thái Validation | Độ trễ |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FTL_01** | **Nhiều điều kiện & Ngoại lệ:** Công ty nợ lương 2 tháng và tự ý chuyển việc, có được nghỉ ngay không? | **ĐẠT** | **ĐẠT** | **ĐẠT** (Điều 35 Khoản 2) | **ĐẠT** (Nêu rõ ngoại lệ Điều 29) | **ĐẠT** | **ĐẠT** (01/01/2021) | **PASSED** | 35.43s |
| **FTL_02** | **Thiếu dữ kiện trọng yếu:** Đang thử việc có phải đóng BHXH bắt buộc không? | **ĐẠT** | **ĐẠT** | **ĐẠT** (Điều 24 BLLĐ, Điều 2 BHXH) | **ĐẠT** | **ĐẠT** (Chỉ ra thiếu loại hình hợp đồng) | **ĐẠT** | **WARNING** (Phân nhánh chuẩn) | 22.82s |
| **FTL_03** | **Phân tầng tỷ lệ:** Ốm thông thường 5 ngày hưởng bao nhiêu %? Có được 65% không? | **ĐẠT** | **ĐẠT** | **ĐẠT** (Điều 45 Khoản 2) | **ĐẠT** (65% chỉ cho bệnh dài ngày $\ge$ 30 năm) | **ĐẠT** | **ĐẠT** | **WARNING** (Chặn gán sai 65%) | 68.86s *(Retry)* |
| **FTL_04** | **Thời điểm hiệu lực:** Tháng 8/2025 sinh con nghỉ mấy tháng, theo luật nào? | **ĐẠT** | **ĐẠT** | **ĐẠT** (Điều 53) | **ĐẠT** | **ĐẠT** | **ĐẠT** (Cảnh báo mốc 01/07/2025) | **PASSED** | 26.56s |
| **FTL_05** | **Văn bản ngoài Knowledge Base:** Nghỉ việc hưởng bảo hiểm thất nghiệp mấy tháng? | **ĐẠT** | **ĐẠT** | **ĐẠT** (Không bịa luật) | **ĐẠT** | **ĐẠT** | **ĐẠT** | **WARNING** (Cảnh báo thiếu căn cứ) | 38.67s |

---

## 6. ĐỐI SOÁNH HỒI QUY TRÊN 10 CÂU HỎI TIÊU BIỂU GIAI ĐOẠN 3

Chạy kiểm thử hồi quy toàn diện qua `tests/test_phase3_agents.py`:
- **Tỷ lệ vượt qua kiểm thử:** **10/10 kịch bản (100%)**.
- **Thời gian phản hồi trung bình:** **20.86 giây / câu hỏi**.
- **Tính toàn vẹn hệ thống:**
  * IntentAgent phân loại chính xác 100% In-Scope và Out-of-Scope (TC10 phản hồi 0.00s).
  * ValidationAgent bảo toàn cơ chế đối chiếu in-memory 1.296 chunks, không phát sinh bất kỳ ngoại lệ nào.
  * ResponseAgent xuất định dạng Markdown 4 phần hoàn chỉnh.

---

## 7. ĐÁNH GIÁ TÀI NGUYÊN VÀ ĐỘ TRỄ

- **Tài nguyên bộ nhớ (RAM Working Set):**
  * Khởi tạo ban đầu: **455.1 MB**.
  * Sau khi nạp LLM Qwen 1.5B GGUF + MiniLM Embedding + ChromaDB: **1.918 MB**.
  * Đỉnh bộ nhớ khi suy luận thực tế (Peak RAM): **2.381 MB** (~2.33 GB).
  * **RAM khả dụng của hệ thống:** Duy trì ổn định trên **2.6 GB**. Không có hiện tượng rò rỉ bộ nhớ (leak) sau nhiều lượt chạy liên tiếp.
- **Độ trễ suy luận (Inference Latency):**
  * Câu hỏi thông thường (150 - 300 tokens): **18.8 - 25.7 giây**.
  * Câu hỏi phức tạp có phân tích dữ kiện và ngoại lệ: **26.5 - 35.4 giây**.
  * Trường hợp kích hoạt Bounded Retry (FTL_03 phát hiện số liệu cần chỉnh lý): **68.8 giây**.
  * *Đánh giá:* Mức độ trễ trung bình ~25 giây là hoàn toàn chấp nhận được và đạt chuẩn cho một hệ thống AI cục bộ chạy trên CPU không có card đồ họa rời.

---

## 8. CÁC GIỚI HẠN CÒN TỒN TẠI (TRANSPARENT LIMITATIONS)

1. **Giới hạn số từ sinh ra trên CPU (LLM Max Tokens):**  
   Với các câu hỏi đa ý phức tạp (vừa hỏi điều kiện, vừa hỏi mức hưởng, vừa hỏi thủ tục), mô hình 1.5B đôi khi phải tóm tắt ngắn gọn để không vượt quá giới hạn 650 tokens, có thể làm cô đọng các bước diễn giải chi tiết.
2. **Khả năng tự tách câu hỏi đa ý của Retrieval:**  
   Fact-to-Law đã giúp LLM nhận diện được nhiều vấn đề pháp lý (Issues), nhưng nếu RetrievalAgent không tìm được đủ cả 2 nhóm chunk cho 2 vế câu hỏi (như Q15 vừa hỏi BLLĐ vừa hỏi Luật BHXH), kết quả phụ thuộc vào việc người dùng tách câu hỏi hoặc cơ chế Query Decomposition trong tương lai.

---

## 9. KẾT LUẬN NGHIỆM THU VÀ ĐỀ XUẤT BƯỚC TIẾP THEO

### 9.1. Kết luận nghiệm thu Phase 4.3
- **ĐẠT YÊU CẦU TOÀN DIỆN:** Đã hiện thực hóa thành công quy trình Fact-to-Law Syllogism trong `LegalAnalysisAgent` mà không cần đổi mô hình, không cần tăng kích thước LLM và không làm tăng số lần gọi mô hình.
- Khả năng nhận diện ngoại lệ, trích xuất dữ kiện, cảnh báo thời điểm hiệu lực và phát hiện dữ kiện còn thiếu đã được xác minh bằng thực nghiệm độc lập.

### 9.2. Đề xuất Phase tiếp theo (Phase 4.4)
> **Khuyến nghị:**  
> Tiến hành **Phase 4.4: Hoàn thiện Bộ kiểm chuẩn Answer Quality Benchmark (25 kịch bản chuẩn hóa có Golden Answers do con người kiểm duyệt)** và đồng bộ hóa các cải tiến BM25 N-gram + Multilingual Dense vào cấu hình chính thức sau khi toàn bộ quy trình kiểm toán độc lập đã hoàn tất.
