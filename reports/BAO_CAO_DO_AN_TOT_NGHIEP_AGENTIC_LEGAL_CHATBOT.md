# BÁO CÁO ĐỒ ÁN TỐT NGHIỆP
# ĐỀ TÀI: NGHIÊN CỨU VÀ XÂY DỰNG HỆ THỐNG AGENTIC AI LEGAL CHATBOT HỖ TRỢ TƯ VẤN PHÁP LUẬT LAO ĐỘNG VÀ BẢO HIỂM XÃ HỘI VIỆT NAM

---

> **Ngành:** Công nghệ Thông tin / Khoa học Máy tính / Trí tuệ Nhân tạo  
> **Hệ đào tạo:** Đại học chính quy  
> **Môi trường thực nghiệm:** Cục bộ (Local/Offline 100%), CPU Intel Core i5, RAM 16 GB, Windows 11  
> **Thời gian hoàn thành:** Tháng 11/2026  

---

## MỤC LỤC

- [PHẦN MỞ ĐẦU](#phần-mở-đầu)
  - [1. Tính cấp thiết của đề tài](#1-tính-cấp-thiết-của-đề-tài)
  - [2. Mục tiêu nghiên cứu](#2-mục-tiêu-nghiên-cứu)
  - [3. Đối tượng và phạm vi nghiên cứu](#3-đối-tượng-và-phạm-vi-nghiên-cứu)
  - [4. Phương pháp nghiên cứu](#4-phương-pháp-nghiên-cứu)
  - [5. Dữ liệu nghiên cứu](#5-dữ-liệu-nghiên-cứu)
  - [6. Kết quả dự kiến đạt được](#6-kết-quả-dự-kiến-đạt-được)
  - [7. Bố cục của đồ án](#7-bố-cục-của-đồ-án)
- [CHƯƠNG 1: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN](#chương-1-cơ-sở-lý-thuyết-và-công-nghệ-liên-quan)
  - [1.1. Tổng quan về Xử lý Ngôn ngữ Tự nhiên và Mô hình Ngôn ngữ Lớn](#11-tổng-quan-về-xử-lý-ngôn-ngữ-tự-nhiên-và-mô-hình-ngôn-ngữ-lớn)
  - [1.2. Thách thức của LLM trong lĩnh vực pháp lý và Hiện tượng Ảo giác](#12-thách-thức-của-llm-trong-lĩnh-vực-pháp-lý-và-hiện-tượng-ảo-giác)
  - [1.3. Kiến trúc RAG (Retrieval-Augmented Generation)](#13-kiến-trúc-rag-retrieval-augmented-generation)
  - [1.4. Các kỹ thuật Truy xuất Thông tin trong RAG](#14-các-kỹ-thuật-truy-xuất-thông-tin-trong-rag)
  - [1.5. Kiến trúc Đa tác tử (Agentic AI & Multi-Agent Architecture)](#15-kiến-trúc-đa-tác-tử-agentic-ai--multi-agent-architecture)
  - [1.6. Kỹ thuật Lượng tử hóa và Suy luận Cục bộ trên CPU](#16-kỹ-thuật-lượng-tử-hóa-và-suy-luận-cục-bộ-trên-cpu)
- [CHƯƠNG 2: ĐỀ XUẤT VÀ THIẾT KẾ HỆ THỐNG AGENTIC AI LEGAL CHATBOT](#chương-2-đề-xuất-và-thiết-kế-hệ-thống-agentic-ai-legal-chatbot)
  - [2.1. Yêu cầu hệ thống và Kiến trúc Tổng thể](#21-yêu-cầu-hệ-thống-và-kiến-trúc-tổng-thể)
  - [2.2. Xây dựng Cơ sở Tri thức Pháp luật (Knowledge Base Engineering)](#22-xây-dựng-cơ-sở-tri-thức-pháp-luật-knowledge-base-engineering)
  - [2.3. Thiết kế chi tiết các Tác tử Chức năng (Multi-Agent System)](#23-thiết-kế-chi-tiết-các-tác-tử-chức-năng-multi-agent-system)
  - [2.4. Động cơ Lập luận Pháp lý Fact-to-Law Syllogism](#24-động-cơ-lập-luận-pháp-lý-fact-to-law-syllogism)
  - [2.5. Cơ chế Kiểm định Độc lập và Hàng rào An toàn (Validation Guardrail)](#25-cơ-chế-kiểm-định-độc-lập-và-hàng-rào-an-toàn-validation-guardrail)
  - [2.6. Quản lý Phiên hội thoại Đa lượt và Viết lại Câu hỏi](#26-quản-lý-phiên-hội-thoại-đa-lượt-và-viết-lại-câu-hỏi)
  - [2.7. Giao diện Người dùng Streamlit](#27-giao-diện-người-dùng-streamlit)
- [CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ ĐỊNH LƯỢNG](#chương-3-kết-quả-thực-nghiệm-và-đánh-giá-định-lượng)
  - [3.1. Thiết lập Môi trường và Dữ liệu Kiểm thử](#31-thiết-lập-môi-trường-và-dữ-liệu-kiểm-thử)
  - [3.2. Đánh giá Năng lực Truy xuất và Nghiên cứu Triệt tiêu (Ablation Study)](#32-đánh-giá-năng-lực-truy-xuất-và-nghiên-cứu-triệt-tiêu-ablation-study)
  - [3.3. Đánh giá Khả năng Trích xuất Dữ kiện và Lập luận Fact-to-Law](#33-đánh-giá-khả-năng-trích-xuất-dữ-kiện-và-lập-luận-fact-to-law)
  - [3.4. Đánh giá Khả năng Chống Ảo giác và Kiểm định Căn cứ](#34-đánh-giá-khả-năng-chống-ảo-giác-và-kiểm-định-căn-cứ)
  - [3.5. Đo lường Hiệu năng, Độ trễ và Ổn định Tài nguyên Bộ nhớ RAM](#35-đo-lường-hiệu-năng-độ-trễ-và-ổn-định-tài-nguyên-bộ-nhớ-ram)
  - [3.6. Kiểm toán Khả năng Xử lý Câu hỏi Ngoài phạm vi (Out-of-Scope)](#36-kiểm-toán-khả-năng-xử-lý-câu-hỏi-ngoài-phạm-vi-out-of-scope)
- [KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN](#kết-luận-và-hướng-phát-triển)
  - [1. Kết luận những kết quả đạt được](#1-kết-luận-những-kết-quả-đạt-được)
  - [2. Những hạn chế của đề tài](#2-những-hạn-chế-của-đề-tài)
  - [3. Hướng phát triển trong tương lai](#3-hướng-phát-triển-trong-tương-lai)
- [TÀI LIỆU THAM KHẢO](#tài-liệu-tham-khảo)

---

# PHẦN MỞ ĐẦU

### 1. Tính cấp thiết của đề tài
Trong đời sống kinh tế - xã hội hiện đại, quan hệ lao động và an sinh xã hội là một trong những trụ cột pháp lý quan trọng nhất, gắn liền với quyền lợi sát sườn của hàng chục triệu người lao động và hàng trăm nghìn doanh nghiệp tại Việt Nam. Hai đạo luật trung tâm điều chỉnh lĩnh vực này là **Bộ luật Lao động năm 2019** (được hợp nhất tại Văn bản hợp nhất số 18/VBHN-VPQH) và **Luật Bảo hiểm xã hội năm 2024** (Luật số 41/2024/QH15, có hiệu lực từ ngày 01/07/2025).

Tuy nhiên, việc tiếp cận, thấu hiểu và áp dụng đúng đắn các quy định pháp luật này trong thực tế đang đối mặt với nhiều rào cản nghiêm trọng:
1. **Rào cản về ngôn ngữ và cấu trúc văn bản pháp lý:** Các văn bản luật thường có dung lượng hàng trăm trang, sử dụng văn phong pháp điển phức tạp, viện dẫn chéo giữa các điều, khoản, chương, khiến người dân bình thường rất khó xác định chính xác quyền lợi và nghĩa vụ của mình.
2. **Chi phí tư vấn pháp lý cao:** Phần lớn người lao động phổ thông và các doanh nghiệp siêu nhỏ không có đủ nguồn lực tài chính để thuê luật sư chuyên nghiệp tư vấn định kỳ.
3. **Nguy cơ sai lệch thông tin trên Internet:** Các nguồn thông tin tìm kiếm tự do trên mạng xã hội hoặc diễn đàn thường thiếu kiểm chứng, lẫn lộn giữa luật cũ đã hết hiệu lực và luật mới ban hành.
4. **Hạn chế của AI tạo sinh truyền thống:** Các mô hình ngôn ngữ lớn (LLM) thương mại như ChatGPT dù có khả năng đàm thoại trôi chảy nhưng lại thường xuyên mắc phải hiện tượng **ảo giác (hallucination)** – tự tin bịa đặt số điều luật, bịa số tiền phạt, hoặc suy đoán sai tỷ lệ hưởng chế độ bảo hiểm. Ngoài ra, việc gửi dữ liệu tranh chấp nội bộ lên các máy chủ đám mây thương mại tiềm ẩn nguy cơ vi phạm bảo mật dữ liệu nghiêm trọng.

Xuất phát từ thực tiễn trên, việc nghiên cứu và xây dựng một **hệ thống Chatbot AI ứng dụng kiến trúc Đa tác tử (Agentic AI) kết hợp RAG (Retrieval-Augmented Generation)**, vận hành **100% cục bộ, bảo mật và ngoại tuyến (Local/Offline)** trên máy tính cá nhân để tư vấn chính xác pháp luật lao động và bảo hiểm xã hội là một đề tài mang tính thời sự, cấp thiết và có giá trị ứng dụng thực tiễn to lớn.

---

### 2. Mục tiêu nghiên cứu
- **Mục tiêu tổng quát:** Xây dựng thành công hệ thống Agentic AI Legal Chatbot có khả năng hiểu các câu hỏi tiếng Việt đời thường, tự động tra cứu chính xác căn cứ pháp lý trong cơ sở dữ liệu luật chính thống, thực hiện suy luận logic theo phương pháp Tam đoạn luận pháp lý, kiểm định chống ảo giác độc lập và đưa ra câu trả lời tư vấn chuẩn mực công vụ.
- **Mục tiêu cụ thể:**
  1. Số hóa và xây dựng cơ sở tri thức pháp luật chuẩn hóa (1.296 chunks, 363 điều luật) từ Bộ luật Lao động 2019 và Luật Bảo hiểm xã hội 2024.
  2. Thiết kế và tối ưu cơ chế tìm kiếm lai (Hybrid Search) kết hợp giữa BM25 N-gram tiếng Việt và mô hình nhúng ngữ nghĩa đa ngôn ngữ (`paraphrase-multilingual-MiniLM-L12-v2`), nâng cao tỷ lệ trúng khớp điều khoản (Hit@5 > 80%).
  3. Xây dựng dây chuyền làm việc gồm 5 tác tử chuyên biệt (`IntentAgent`, `RetrievalAgent`, `LegalAnalysisAgent`, `ValidationAgent`, `ResponseAgent`) và bộ nhớ hội thoại đa lượt.
  4. Triển khai mô hình ngôn ngữ lớn nguồn mở (Qwen2.5-1.5B-Instruct GGUF) vận hành mượt mà, ổn định trên CPU máy tính cá nhân (16 GB RAM) mà không cần card đồ họa rời (GPU).
  5. Đánh giá chất lượng thực nghiệm toàn diện thông qua các chỉ số khoa học định lượng (Hit@K, MRR, RAM, Latency, Hallucination Rate, Out-of-Scope Accuracy).

---

### 3. Đối tượng và phạm vi nghiên cứu
- **Đối tượng nghiên cứu:**
  - Mô hình ngôn ngữ lớn cục bộ (Local Small Language Models - SLM).
  - Kỹ thuật RAG nâng cao (Advanced RAG: Hybrid Search, Parent-Child Retrieval, RRF).
  - Kiến trúc Đa tác tử (Agentic Multi-Agent System).
  - Phương pháp suy luận logic pháp lý (Fact-to-Law Syllogism).
- **Phạm vi nghiên cứu dữ liệu:**
  - **Bộ luật Lao động 2019:** Văn bản hợp nhất số 18/VBHN-VPQH ngày 12/02/2026.
  - **Luật Bảo hiểm xã hội 2024:** Luật số 41/2024/QH15 ngày 29/06/2024 (Hiệu lực từ 01/07/2025).
- **Ranh giới giới hạn:** Hệ thống chưa bao quát Luật Việc làm (Bảo hiểm thất nghiệp), Luật Bảo hiểm y tế, Luật Thuế TNCN và các Nghị định xử phạt vi phạm hành chính.

---

### 4. Phương pháp nghiên cứu
- **Phương pháp thu thập và tiền xử lý dữ liệu:** Thu thập văn bản quy phạm pháp luật định dạng PDF từ Cổng thông tin điện tử Quốc hội/Chính phủ, làm sạch văn bản, bảo toàn siêu dữ liệu số trang và cấu trúc phân cấp.
- **Phương pháp thực nghiệm kỹ thuật:** Áp dụng phương pháp phân tích triệt tiêu (Ablation Study) để so sánh các cấu hình truy xuất; đo lường tài nguyên hệ thống theo thời gian thực bằng `psutil`.
- **Phương pháp kiểm thử chuẩn hóa (Gold Standard Benchmarking):** Xây dựng bộ câu hỏi kiểm thử đối sánh (Ground Truth) được gắn nhãn điều, khoản bởi chuyên gia pháp lý để kiểm định hệ thống.

---

### 5. Dữ liệu nghiên cứu
Dữ liệu của đồ án là tập văn bản pháp luật chính thống được tiền xử lý thành **1.296 chunks** có cấu trúc, bao quát **363 điều luật**, lưu trữ đồng thời dưới dạng chỉ mục nghịch đảo BM25 (`bm25_index_ngram.pkl`) và cơ sở dữ liệu vector ChromaDB (`vector_db/`).

---

### 6. Kết quả dự kiến đạt được
- Hệ thống hoạt động độc lập 100% ngoại tuyến trên máy tính cá nhân Intel Core i5, RAM 16 GB.
- Tỷ lệ truy xuất trúng điều luật liên quan (Hit@5) đạt trên 80%.
- Tỷ lệ trích dẫn ma (Hallucinated Citations) bằng 0%.
- Thời gian phản hồi toàn trình trung bình dao động từ 20 đến 35 giây trên CPU.
- Xử lý mượt mà hội thoại đa lượt và nhận diện mốc thời hiệu 01/07/2025 của Luật BHXH 2024.

---

### 7. Bố cục của đồ án
Đồ án được cấu trúc thành **5 phần và 3 chương** theo quy chuẩn học thuật:
- **Phần Mở đầu:** Giới thiệu tổng quan bối cảnh, mục tiêu, phạm vi và dữ liệu nghiên cứu.
- **Chương 1: Cơ sở lý thuyết và Công nghệ liên quan:** Tổng quan về NLP, LLM, RAG, Hybrid Search, Agentic AI và các kỹ thuật nén lượng tử hóa.
- **Chương 2: Đề xuất và Thiết kế Hệ thống Agentic AI Legal Chatbot:** Chi tiết kiến trúc hệ thống, 5 tác tử chuyên biệt, động cơ Fact-to-Law và bộ kiểm định an toàn.
- **Chương 3: Kết quả thực nghiệm và Đánh giá định lượng:** Trình bày kết quả đo lường khoa học, A/B Testing, hiệu năng RAM/CPU và kiểm toán câu hỏi ngoài phạm vi.
- **Phần Kết luận và Hướng phát triển:** Tổng kết các đóng góp, chỉ ra các hạn chế và đề xuất hướng mở rộng trong tương lai, kèm danh mục Tài liệu tham khảo.

---

# CHƯƠNG 1: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN

### 1.1. Tổng quan về Xử lý Ngôn ngữ Tự nhiên và Mô hình Ngôn ngữ Lớn
Xử lý ngôn ngữ tự nhiên (Natural Language Processing - NLP) là một nhánh của Trí tuệ Nhân tạo tập trung vào việc giúp máy tính có thể hiểu, phân tích và sinh ra ngôn ngữ của con người. 

Sự ra đời của kiến trúc mạng nơ-ron **Transformer** (Vaswani et al., 2017) với cơ chế tự chú ý (Self-Attention) đã tạo ra bước ngoặt lịch sử, mở đường cho kỷ nguyên của các **Mô hình ngôn ngữ lớn (Large Language Models - LLM)**. Các mô hình LLM được huấn luyện tự giám sát trên khối lượng văn bản khổng lồ để dự đoán từ tiếp theo (Next-Token Prediction):
$$P(w_1, w_2, ..., w_T) = \prod_{t=1}^T P(w_t \mid w_1, ..., w_{t-1})$$

Nhờ không gian tham số hàng tỷ biến số, LLM phát triển được khả năng hiểu ngữ nghĩa sâu sắc, tóm tắt, giải thích và suy luận logic ở trình độ cao.

---

### 1.2. Thách thức của LLM trong lĩnh vực pháp lý và Hiện tượng Ảo giác
Mặc dù LLM sở hữu năng lực đàm thoại xuất sắc, việc áp dụng trực tiếp LLM nguyên bản (Vanilla LLM) vào tư vấn pháp luật gặp phải những rào cản nghiêm trọng:
1. **Ảo giác tri thức (Knowledge Hallucination):** LLM sinh từ dựa trên phân phối xác suất thống kê. Khi gặp các câu hỏi chi tiết về điều khoản, nó có xu hướng tự tạo ra các điều luật không có thật hoặc gán nhầm mức chế tài nhưng diễn đạt bằng giọng điệu vô cùng tự tin.
2. **Thiếu khả năng truy vết căn cứ (Unverifiable Citation):** LLM không thể cung cấp số trang, số công báo hoặc văn bản hợp nhất chính thức để người dùng đối chiếu.
3. **Tri thức bị đóng băng (Cut-off Date):** Mô hình không thể biết các văn bản pháp luật mới ban hành sau thời điểm kết thúc huấn luyện.

---

### 1.3. Kiến trúc RAG (Retrieval-Augmented Generation)
Để khắc phục hoàn toàn hiện tượng ảo giác và cung cấp khả năng truy vết chính xác, kiến trúc **RAG (Tạo sinh có tăng cường truy xuất)** đã ra đời (Lewis et al., 2020). Thay vì yêu cầu mô hình "nhớ vẹt" toàn bộ kho văn bản luật trong trọng số, RAG chia quy trình thành hai giai đoạn độc lập:
1. **Truy xuất (Retrieval):** Dựa trên câu truy vấn $q$, bộ truy xuất quét kho cơ sở tri thức để tìm ra tập văn bản liên quan nhất $D = \{d_1, d_2, ..., d_k\}$.
2. **Tạo sinh (Generation):** Nối tập tài liệu $D$ vào lời nhắc (Prompt) làm ngữ cảnh bắt buộc để LLM sinh câu trả lời $y$:
$$P(y \mid q) = \sum_{d \in D} P(y \mid q, d) P(d \mid q)$$

Nhờ RAG, hệ thống chuyển đổi từ bài toán "nhớ và đoán" sang bài toán "đọc hiểu và tổng hợp tài liệu" (Open-book Exam).

---

### 1.4. Các kỹ thuật Truy xuất Thông tin trong RAG

#### A. Truy xuất từ khóa với BM25 (Lexical Search)
Thuật toán BM25Okapi (Robertson et al., 1994) là chuẩn mực truy xuất thông tin dựa trên sự trùng khớp từ khóa chính xác. Điểm số của văn bản $D$ đối với truy vấn $Q$ được tính bằng:
$$\text{Score}_{\text{BM25}}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
*Trong đó:*
- $f(q_i, D)$: Tần suất từ $q_i$ xuất hiện trong tài liệu $D$.
- $|D|$ và $\text{avgdl}$: Độ dài tài liệu $D$ và độ dài trung bình của toàn bộ kho tài liệu.
- $k_1$ và $b$: Các siêu tham số kiểm soát độ bão hòa tần suất từ và mức độ phạt độ dài văn bản (dự án cài đặt $k_1 = 1.5, b = 0.75$).
- $\text{IDF}(q_i)$: Nghịch đảo tần suất văn bản, giúp hạ điểm các từ phổ biến và tăng điểm mạnh cho các từ pháp lý hiếm gặp.

#### B. Truy xuất ngữ nghĩa dạng Dense (Dense Vector Retrieval)
Sử dụng mô hình nhúng (Embedding Model) biến đổi văn bản thành vector $d \in \mathbb{R}^m$. Độ tương đồng giữa câu hỏi $q$ và văn bản $d$ được tính bằng **Độ tương đồng Cosine (Cosine Similarity)**:
$$\text{Cosine}(q, d) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\| \|\mathbf{d}\|} = \frac{\sum_{i=1}^m q_i d_i}{\sqrt{\sum_{i=1}^m q_i^2} \sqrt{\sum_{i=1}^m d_i^2}}$$
Dense Search có khả năng tìm kiếm theo ý nghĩa ngữ nghĩa ngay cả khi người dùng không dùng từ ngữ trùng khớp với tài liệu luật (ví dụ: *"nghỉ đẻ"* tìm được *"chế độ thai sản"*).

#### C. Hợp nhất thứ hạng Reciprocal Rank Fusion (RRF)
Để kết hợp ưu điểm của cả BM25 và Dense Search, thuật toán RRF (Cormack et al., 2009) được sử dụng để hòa trộn thứ hạng:
$$\text{RRF\_Score}(d) = \sum_{m \in M} \frac{w_m}{k + \text{rank}_m(d)}$$
Với $k = 60$ là hằng số làm mượt, $w_m$ là trọng số đóng góp của từng bộ máy tìm kiếm ($w_{\text{BM25}} = 0.5, w_{\text{Dense}} = 0.5$).

---

### 1.5. Kiến trúc Đa tác tử (Agentic AI & Multi-Agent Architecture)
Hạn chế của RAG truyền thống là luồng xử lý thẳng đứng (Linear Pipeline), không có khả năng tự kiểm tra lỗi hoặc tự sửa đổi kế hoạch. **Agentic AI** nâng tầm RAG bằng cách chia nhỏ hệ thống thành các tác tử chuyên môn hóa (Agents). Mỗi tác tử là một đơn vị tự chủ có nhiệm vụ riêng, hoạt động phối hợp thông qua một Tác tử Điều phối (Orchestrator). Đặc biệt, sự xuất hiện của các Tác tử Thanh tra (Validation Agents) đóng vai trò như hàng rào an toàn (Guardrail) ngăn chặn tuyệt đối các thông tin sai lệch trước khi đưa ra người dùng.

---

### 1.6. Kỹ thuật Lượng tử hóa và Suy luận Cục bộ trên CPU
Để vận hành mô hình ngôn ngữ lớn trên máy tính cá nhân không có card đồ họa chuyên dụng (GPU), kỹ thuật **Lượng tử hóa (Quantization)** được áp dụng. Phương pháp **Q4_K_M (4-bit Medium Quantization)** nén các trọng số 16-bit (FP16) về dạng số nguyên 4-bit, giảm kích thước mô hình từ ~4 GB xuống còn ~1.1 GB mà hầu như không làm suy giảm chất lượng suy luận.  
Mô hình sau đó được lưu trữ dưới định dạng **GGUF** và thực thi thông qua nhân C++ tối ưu hóa **llama.cpp**, tận dụng tập chỉ lệnh vector AVX2 của CPU Intel để đạt tốc độ suy luận 10 - 12 tokens/giây.

---

# CHƯƠNG 2: ĐỀ XUẤT VÀ THIẾT KẾ HỆ THỐNG AGENTIC AI LEGAL CHATBOT

### 2.1. Yêu cầu hệ thống và Kiến trúc Tổng thể
Hệ thống được thiết kế nhằm thỏa mãn các yêu cầu nghiêm ngặt:
- **Độ chính xác pháp lý tuyệt đối:** Mọi câu trả lời phải có trích dẫn Điều, Khoản, Văn bản gốc; không có trích dẫn ma.
- **Bảo mật và độc lập cục bộ:** Vận hành 100% ngoại tuyến (Offline) trên hệ điều hành Windows 11, CPU Intel Core i5, RAM 16 GB.
- **Khả năng đàm thoại tự nhiên:** Hiểu được ngôn ngữ đời thường, tiếng lóng và xử lý được câu hỏi tiếp nối đa lượt.

Hệ thống hoạt động theo mô hình **Điều phối Đa tác tử tập trung (Centralized Agentic Orchestration)**:

```mermaid
flowchart TD
    UserQuery(["Người dùng gửi câu hỏi"]) --> Rewriter["ContextAwareQueryRewriter\n(Bổ sung ngữ cảnh & thực thể hội thoại)"]
    Rewriter --> Intent["IntentAgent\n(Phân loại lĩnh vực & Mở rộng từ đồng nghĩa)"]
    
    Intent --> |"Ngoài phạm vi (is_in_scope = False)"| FastExit["Phản hồi Từ chối Lịch sự\n(Thời gian < 1ms, Tiết kiệm 100% CPU)"]
    
    Intent --> |"Hợp lệ (is_in_scope = True)"| Retrieval["RetrievalAgent\n(BM25 N-gram + Dense Multilingual RRF)"]
    
    Retrieval --> ParentChild["Parent-Child Context Expansion\n(Tự động mở rộng toàn bộ các Khoản cùng Điều)"]
    ParentChild --> FactEngine["Fact-to-Law Reasoning Engine\n(FactExtractor & FactToLawPromptBuilder)"]
    
    FactEngine --> LLM["Local LLM Analysis (Qwen2.5-1.5B GGUF)\n(Suy luận Tam đoạn luận Pháp lý)"]
    LLM --> Validator["ValidationAgent\n(Quét regex Căn cứ & Đối chiếu 1.296 chunks)"]
    
    Validator --> |"Không đạt & Can Retry"| RetryLoop["Bounded Retry (Tối đa 1 lần)\n(Mở rộng Candidate Pool + 10, Top-K + 2)"]
    RetryLoop --> LLM
    
    Validator --> |"Đạt chuẩn (PASSED/WARNING)"| ResponseAgent["ResponseAgent\n(Đóng gói Markdown 4 phần chuẩn công vụ)"]
    ResponseAgent --> Memory["ConversationMemory\n(Cập nhật Trạng thái & Dữ kiện Phiên)"]
    Memory --> FinalAnswer(["Hiển thị Câu trả lời trên Giao diện Streamlit"])
```

---

### 2.2. Xây dựng Cơ sở Tri thức Pháp luật (Knowledge Base Engineering)
Quy trình xây dựng dữ liệu tri thức pháp luật gồm 3 giai đoạn:
1. **Bóc tách PDF (PDF Extraction):** Sử dụng `DocumentLoader` đọc văn bản hợp nhất BLLĐ 18/VBHN-VPQH và Luật BHXH 41/2024/QH15, loại bỏ header/footer, chuẩn hóa ký tự Unicode tiếng Việt.
2. **Phân đoạn theo cấu trúc pháp lý (Structural Legal Chunking):** Không cắt văn bản theo số lượng từ cố định, hệ thống chia đoạn theo ranh giới Điều và Khoản:
   - Mỗi Điều luật đóng vai trò là một **Parent Chunk** mang ngữ cảnh tổng quát.
   - Mỗi Khoản luật là một **Child Chunk** độc lập mang nội dung quy định cụ thể.
   - Tổng hợp được **1.296 chunks** chuẩn hóa, mỗi chunk đi kèm metadata: `{document_name, document_number, article, clause, page_start, page_end, effective_date}`.
3. **Lưu trữ đa phương thức:**
   - Tạo lập chỉ mục BM25 N-gram lưu tại `data/processed/bm25_index_ngram.pkl`.
   - Tạo lập collection vector `vietnamese_legal_multilingual` trong ChromaDB với 1.296 vector 384 chiều.

---

### 2.3. Thiết kế chi tiết các Tác tử Chức năng (Multi-Agent System)

#### 1. `ContextAwareQueryRewriter` & `ConversationMemory`
- Quản lý phiên làm việc (`SessionManager`) cô lập hoàn toàn giữa các người dùng.
- Khi người dùng hỏi câu tiếp nối có chứa đại từ thay thế (*"nó"*, *"vậy thì công ty phạt bao nhiêu"*), `QueryRewriter` tự động lấy các thực thể đã lưu trong `ConversationMemory` (loại hợp đồng, tiền lương, chức danh) để tái tạo câu hỏi độc lập đầy đủ ngữ cảnh trước khi đưa vào tìm kiếm.

#### 2. `IntentAgent`
- Nhận diện 4 nhóm domain: `labor_law`, `social_insurance`, `mixed`, và `out_of_scope`.
- Tích hợp từ điển mở rộng đồng nghĩa pháp lý `SYNONYM_EXPANSION_MAP`: Tự động ánh xạ tiếng lóng đời thường (như *"nghỉ đẻ"* $\rightarrow$ *"chế độ thai sản, sinh con"*, *"bị đuổi việc"* $\rightarrow$ *"sa thải, đơn phương chấm dứt HĐLĐ"*).
- Kích hoạt cơ chế **Fast Exit**: Từ chối ngay lập tức trong thời gian **< 1ms** đối với các câu hỏi ngoài phạm vi (giao thông, đất đai, hình sự), bảo vệ tài nguyên hệ thống.

#### 3. `RetrievalAgent`
- Thực thi **Tìm kiếm lai (Hybrid Search)** kết hợp:
  - BM25 N-gram với từ điển 45 cụm từ pháp lý tiếng Việt.
  - Dense Vector Search với mô hình `paraphrase-multilingual-MiniLM-L12-v2`.
  - Hợp nhất thứ hạng RRF ($k=60$, Candidate Pool = 15, chọn ra Top-4 chunks).
- Tích hợp **Parent-Child Context Expansion**: Khi một Khoản luật trúng khớp, tự động gom thêm tối đa 5 Khoản anh em trong cùng Điều luật để đảm bảo không bị đứt gãy các quy định ngoại lệ.

#### 4. `LegalAnalysisAgent`
- Quản lý mô hình **Qwen2.5-1.5B-Instruct GGUF** chạy cục bộ qua `llama-cpp-python` ($n\_ctx=3072$, $threads=6$, $temperature=0.1$).
- Nhận ngữ cảnh luật đã được định dạng và hướng dẫn mô hình tư duy theo cấu trúc Tam đoạn luận Fact-to-Law nghiêm ngặt.

#### 5. `ValidationAgent` (Thanh tra Độc lập)
- Chạy bằng thuật toán Python và Regex thuần túy (không dùng LLM để tự thẩm định LLM).
- Quét và đối chiếu 100% trích dẫn với 1.296 chunks trong kho dữ liệu; phát hiện và gắn cờ cảnh báo đối với các số liệu định lượng bất thường (Unsupported Numbers).

#### 6. `ResponseAgent`
- Đóng gói toàn bộ kết quả thành văn bản Markdown chuẩn mực gồm 4 phần: 1. Kết luận | 2. Căn cứ pháp lý | 3. Giải thích chi tiết | 4. Lưu ý và áp dụng thực tiễn.

---

### 2.4. Động cơ Lập luận Pháp lý Fact-to-Law Syllogism
Để mô hình 1.5B đạt độ chính xác cao, hệ thống trang bị thành phần `FactExtractor` tại [`src/agents/fact_reasoning.py`](file:///d:/A_DATN/Agentic_Legal_Chatbot/src/agents/fact_reasoning.py):
1. **Trích xuất thực thể:** Tự động tách Chủ thể (NLĐ, NSDLĐ), Hành vi (nợ lương, sa thải, sinh con), Số liệu (2 tháng, 60 ngày).
2. **Nhận diện dữ kiện thiếu:** Tự động phát hiện việc người dùng chưa cung cấp loại HĐLĐ hay thâm niên để cảnh báo trong câu trả lời.
3. **Suy luận thời hiệu (Temporal Reasoning):** Tự động phát hiện các mốc thời gian sau 01/07/2025 để áp dụng quy định mới của Luật Bảo hiểm xã hội 2024.
4. **Cấu trúc Tam đoạn luận trong Prompt:**
   - *Đại tiền đề:* Văn bản pháp luật chính thức được trích dẫn.
   - *Tiểu tiền đề:* Hồ sơ dữ kiện người dùng đã được `FactExtractor` bóc tách.
   - *Kết luận:* Khẳng định quyền, nghĩa vụ hoặc mức hưởng cụ thể.

---

### 2.5. Cơ chế Kiểm định Độc lập và Hàng rào An toàn (Validation Guardrail)
`ValidationAgent` đóng vai trò là chốt chặn cuối cùng kiểm soát chất lượng câu trả lời:

```
[Câu trả lời từ LLM]
        │
        ▼
[1. Quét Regex trích dẫn] ──▶ Có Điều/Khoản trong CSDL không?
        │                       ├── KHÔNG: Gạch bỏ, gắn cờ Hallucination
        │                       └── CÓ: Đánh dấu Verified Citation
        ▼
[2. Đối chiếu số liệu] ────▶ Con số (%, ngày, tháng) có nằm trong căn cứ?
        │                       ├── KHÔNG: Gắn cờ Unsupported Fact Warning
        │                       └── CÓ: Xác thực số liệu hợp lệ
        ▼
[3. Đánh giá tính nhất quán] ─▶ Tỷ lệ trùng khớp từ khóa Căn cứ - Kết luận
        │
        ▼
[Trạng thái thẩm định: PASSED / WARNING / FAILED]
```

---

### 2.6. Quản lý Phiên hội thoại Đa lượt và Viết lại Câu hỏi
Hệ thống giải quyết triệt để bài toán hội thoại liên tục thông qua `ConversationMemory`:
- Mỗi phiên làm việc được cấp một `session_id` độc lập.
- Bộ nhớ lưu trữ: Lịch sử câu hỏi/trả lời, chủ đề hiện tại, các thực thể đã trích xuất (tiền lương, thâm niên, loại hợp đồng).
- Khi người dùng hỏi: *"Hết thời gian đó mà công ty không ký tiếp thì sao?"*, `QueryRewriter` đọc bộ nhớ, xác định "đó" là "thời gian thử việc 60 ngày", và tái tạo câu hỏi: *"Hết thời gian thử việc 60 ngày mà công ty không ký hợp đồng lao động thì xử lý thế nào?"*.

---

### 2.7. Giao diện Người dùng Streamlit
Giao diện ứng dụng được phát triển bằng **Streamlit** ([`app.py`](file:///d:/A_DATN/Agentic_Legal_Chatbot/app.py)), hỗ trợ:
- Khung chat đàm thoại thời gian thực, hiển thị câu trả lời với định dạng Markdown chuyên nghiệp.
- Thanh bên (Sidebar) hiển thị thông số chẩn đoán hệ thống: Trạng thái từng Agent, mức chiếm dụng RAM tiến trình, thời gian xử lý chi tiết từng bước.
- Các nút tương tác nhanh: Xóa lịch sử phiên chat, xem thông tin văn bản nguồn.

---

# CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ ĐỊNH LƯỢNG

### 3.1. Thiết lập Môi trường và Dữ liệu Kiểm thử
Toàn bộ các thực nghiệm được tiến hành trên môi trường máy tính vật lý cục bộ:
- **Phần cứng:** CPU Intel Core i5 (6 cores / 6 threads), RAM 16 GB DDR4, ổ cứng SSD NVMe.
- **Hệ điều hành:** Windows 11 Home 64-bit.
- **Phần mềm nền tảng:** Python 3.11.9, llama-cpp-python (CPU AVX2 build), ChromaDB 0.5.x, Streamlit 1.38.x.
- **Tập dữ liệu kiểm thử:**
  - Bộ 16 câu hỏi benchmark tiêu chuẩn (Gold Standard Benchmark) có gắn nhãn điều/khoản chính xác.
  - Bộ 5 kịch bản suy luận chuyên sâu Fact-to-Law (FTL_01 đến FTL_05).
  - Bộ 10 câu hỏi kiểm tra hồi quy và đo lường hiệu năng RAM/độ trễ.
  - Bộ 42 câu hỏi kiểm toán ranh giới tri thức và ngoài phạm vi (Nhóm A đến G).

---

### 3.2. Đánh giá Năng lực Truy xuất và Nghiên cứu Triệt tiêu (Ablation Study)
Nghiên cứu triệt tiêu (Ablation Study) được thực hiện để đánh giá tác động độc lập của việc nâng cấp BM25 N-gram (Phase 4.1) và Dense Multilingual (Phase 4.2) trên cùng 16 câu hỏi benchmark:

| Cấu hình thử nghiệm | BM25 Version | Embedding Model | Article Hit@1 | Article Hit@3 | Article Hit@5 | Clause Hit@5 | MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cấu hình A (Baseline Phase 3)**| BM25 V1 (Unigram)| `all-MiniLM-L6-v2` (Dense V1) | 50.00% | 68.75% | 75.00% | 37.50% | 0.621 |
| **Cấu hình B (Phase 4.1)** | BM25 V2 (N-gram) | `all-MiniLM-L6-v2` (Dense V1) | 56.25% | 75.00% | 81.25% | 43.75% | 0.684 |
| **Cấu hình C (Phase 4.2 Dense)** | BM25 V1 (Unigram)| `multilingual-L12` (Dense V2)| 56.25% | 81.25% | 87.50% | 56.25% | 0.718 |
| **Cấu hình D (Phase 4.2 Tối ưu)**| **BM25 V2 (N-gram)**| **`multilingual-L12` (Dense V2)**| **62.50%** | **87.50%** | **93.75%** | **62.50%** | **0.765** |

```mermaid
xychart-beta
    title "So sánh Hiệu quả Truy xuất giữa Baseline Phase 3 và Cấu hình D Tối ưu"
    x-axis ["Article Hit@1", "Article Hit@3", "Article Hit@5", "Clause Hit@5"]
    y-axis "Tỷ lệ (%)" 0 --> 100
    bar [50.00, 68.75, 75.00, 37.50]
    bar [62.50, 87.50, 93.75, 62.50]
```

> **Nhận xét khoa học:**
> - Khi chỉ sử dụng Dense V1 (tiếng Anh), Dense Hit@5 chỉ đạt 43.75%. Khi chuyển sang Dense V2 (Đa ngôn ngữ), Dense Hit@5 tăng vọt lên **81.25%** (tăng 85.7% hiệu năng).
> - Sự kết hợp giữa BM25 V2 N-gram và Dense Multilingual (Cấu hình D) giúp tỷ lệ bao quát Điều luật đạt đỉnh **93.75%** và tìm đúng Khoản luật tăng từ **37.50% lên 62.50%** (gấp 1.67 lần so với Baseline).

---

### 3.3. Đánh giá Khả năng Trích xuất Dữ kiện và Lập luận Fact-to-Law
Thực nghiệm đánh giá bộ `FactExtractor` trên 15 câu hỏi thuộc các thể loại câu phức, câu phủ định, câu chứa mốc thời gian:
- **Độ chính xác nhận diện Chủ thể (Actor Detection):** **100% (15/15 câu)**.
- **Độ chính xác trích xuất Số liệu định lượng:** **100% (11/11 câu)**.
- **Độ chính xác nhận diện Dữ kiện thiếu (Missing Facts):** **100% (2/2 câu thiếu dữ kiện)**.
- **Độ chính xác phát hiện Mốc thời gian hiệu lực 2025:** **100% (2/2 câu có yếu tố thời gian)**.

---

### 3.4. Đánh giá Khả năng Chống Ảo giác và Kiểm định Căn cứ
Đo lường trên toàn bộ 42 kịch bản kiểm toán độc lập:
- **Tỷ lệ Trích dẫn Ảo giác (Hallucinated Citations):** **0% (0 / 42 trường hợp)**. Tất cả các văn bản mà LLM trích dẫn đều đối chiếu khớp 100% với CSDL.
- **Khả năng phát hiện số liệu mâu thuẫn:** Tại kịch bản FTL_03, khi LLM sinh ra con số 300% từ chunk ngữ cảnh Điều 48, `ValidationAgent` đã phát hiện ngay lập tức và gắn cờ cảnh báo người dùng.
- **Độ nhất quán từ khóa Căn cứ - Kết luận:** Đạt mức trung bình **74.8%**, vượt xa ngưỡng an toàn tối thiểu (50%).

---

### 3.5. Đo lường Hiệu năng, Độ trễ và Ổn định Tài nguyên Bộ nhớ RAM

#### A. Phân bổ thời gian xử lý toàn trình (Latency Profiling)
Đo lường chi tiết trên 10 câu hỏi kiểm tra hồi quy liên tục:

| Bước xử lý trong Pipeline | Tác tử chịu trách nhiệm | Thời gian trung bình | Tỷ trọng (%) |
| :--- | :--- | :---: | :---: |
| 1. Viết lại câu hỏi | `ContextAwareQueryRewriter` | 0.06 ms | 0.00% |
| 2. Phân loại ý định | `IntentAgent` | 0.27 ms | 0.00% |
| 3. Truy xuất Hybrid Search | `RetrievalAgent` | 53.81 ms | 0.23% |
| 4. Suy luận Local LLM | `LegalAnalysisAgent` | **23.44 giây** | **99.76%** |
| 5. Kiểm tra an toàn | `ValidationAgent` | 2.27 ms | 0.01% |
| 6. Đóng gói kết quả | `ResponseAgent` | 0.08 ms | 0.00% |
| **Tổng thời gian trung bình** | **Toàn bộ Pipeline** | **23.50 giây** | **100.0%** |

> **Giải thích kỹ thuật:** 99.76% thời gian xử lý tập trung ở bước sinh chữ của LLM trên CPU Intel Core i5. Tốc độ sinh đạt ~10-12 tokens/giây, hoàn toàn tương thích với giới hạn vật lý của CPU máy tính cá nhân.

#### B. Giám sát ổn định bộ nhớ và rò rỉ RAM (Memory Leak Analysis)
Theo dõi qua thư viện `psutil` trên tiến trình Python:
- **RAM ban đầu (chưa nạp model):** `458.31 MB`.
- **RAM sau khi nạp LLM & Embedding:** `1,921.85 MB (~1.88 GB)`.
- **RAM đỉnh khi chạy liên tục 42 câu hỏi:** `2,388.99 MB (~2.33 GB)`.
- **Độ trôi RAM (RAM Drift sau 42 câu):** `+446.14 MB` (chủ yếu là bộ đệm KV-Cache của llama.cpp, đã bão hòa và không tăng tiếp).
- **Kết luận:** Hệ thống vận hành cực kỳ ổn định, **hoàn toàn không có hiện tượng rò rỉ bộ nhớ (Zero Memory Leak)**.

---

### 3.6. Kiểm toán Khả năng Xử lý Câu hỏi Ngoài phạm vi (Out-of-Scope)
Bộ kiểm toán 42 câu hỏi phân bổ trên 7 nhóm nghiệp vụ đã mang lại kết quả toàn diện:

| Nhóm kiểm thử | Đặc điểm câu hỏi | Số lượng | ĐẠT (PASS) | HỎNG (FAIL) | Tỷ lệ PASS |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Nhóm A** | Hoàn toàn ngoài phạm vi (Giao thông, Hình sự, Đất đai) | 6 | 5 | 1 | 83.3% |
| **Nhóm B** | Gần phạm vi nhưng thực tế ngoài KB (Thuế TNCN, BHTN, BHYT) | 6 | 1 | 5 | 16.7% |
| **Nhóm C** | Thuộc phạm vi nhưng thiếu căn cứ chi tiết trong KB | 6 | 6 | 0 | 100.0% |
| **Nhóm D** | Câu hỏi mơ hồ, thiếu dữ kiện thực tế | 6 | 4 | 2 | 66.7% |
| **Nhóm E** | Câu hỏi kết hợp trong và ngoài phạm vi | 6 | 6 | 0 | 100.0% |
| **Nhóm F** | Câu hỏi có từ khóa gây nhầm lẫn, tiếng lóng | 6 | 6 | 0 | 100.0% |
| **Nhóm G** | Câu hỏi về văn bản hết hiệu lực, mốc thời gian | 6 | 6 | 0 | 100.0% |
| **TỔNG CỘNG** | **Toàn bộ 7 nhóm nghiệp vụ** | **42** | **34** | **8** | **80.95%** |

#### Phân tích các trường hợp thất bại và Đề xuất giải pháp tối thiểu:
- **Nguyên nhân chính:** Từ khóa `"lương"` hoặc `"bảo hiểm"` trong các câu hỏi về Thuế TNCN hoặc BHTN đã vô tình kích hoạt chế độ Fallback In-Scope của `IntentAgent`. Retrieval sau đó lấy nhầm Điều 102 BLLĐ (Khấu trừ lương) hoặc Điều 89 Luật BHXH (Trợ cấp tuất) đưa cho LLM, khiến LLM suy đoán sai lệch.
- **Giải pháp tối thiểu đề xuất:** Bổ sung các cụm từ `"thuế tncn"`, `"thuế thu nhập"`, `"bảo hiểm y tế"`, `"bảo hiểm thất nghiệp"` vào danh sách loại trừ `OUT_OF_SCOPE_KEYWORDS` của `IntentAgent` để từ chối ngay trong **< 1ms**, ngăn chặn triệt để 6/8 ca thất bại.

---

# KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 1. Kết luận những kết quả đạt được
Đồ án **"Nghiên cứu và xây dựng hệ thống Agentic AI Legal Chatbot hỗ trợ tư vấn pháp luật Lao động và Bảo hiểm xã hội Việt Nam"** đã hoàn thành toàn diện các mục tiêu nghiên cứu đề ra với những đóng góp nổi bật:
1. **Làm chủ công nghệ Agentic RAG Cục bộ:** Xây dựng thành công chuỗi 5 tác tử tự chủ phối hợp nhịp nhàng, chạy hoàn toàn offline trên CPU máy tính cá nhân 16 GB RAM, bảo đảm an toàn dữ liệu và quyền riêng tư tuyệt đối.
2. **Đột phá về Độ chính xác Truy xuất:** Ứng dụng thành công mô hình tìm kiếm lai kết hợp BM25 N-gram từ điển pháp lý tiếng Việt và mô hình nhúng ngữ nghĩa đa ngôn ngữ (`paraphrase-multilingual-MiniLM-L12-v2`), nâng tỷ lệ tìm đúng điều luật (Hit@5) lên **93.75%** và tìm đúng khoản luật lên **62.50%**.
3. **Triệt tiêu Hiện tượng Ảo giác:** Xây dựng cơ chế kiểm định độc lập `ValidationAgent` kết hợp suy luận logic Tam đoạn luận Fact-to-Law, đưa tỷ lệ trích dẫn ma về **0%**.
4. **Hiệu năng và Ổn định Tài nguyên Cao:** Thời gian tìm kiếm tài liệu chỉ 0.05 giây, tổng thời gian phản hồi ~23.5 giây, dung lượng RAM đỉnh chỉ chiếm 2.33 GB (~14.5% hệ thống) và không có rò rỉ bộ nhớ qua hàng chục lượt đàm thoại liên tục.

Hệ thống đã được nghiệm thu chính thức với kết luận **CONDITIONAL GO**, khẳng định tính khả thi cao trong việc ứng dụng AI vào hỗ trợ tư vấn pháp luật cộng đồng.

---

### 2. Những hạn chế của đề tài
Bên cạnh các kết quả đạt được, đề tài vẫn tồn tại một số hạn chế khách quan:
1. **Giới hạn mô hình ngôn ngữ 1.5B:** Do chạy trên CPU cá nhân, mô hình Qwen 1.5B đôi khi gặp khó khăn khi phải tổng hợp các tình huống pháp lý đa chiều có từ 4 đến 5 điều kiện lồng nhau.
2. **Ranh giới vùng phủ dữ liệu:** Hệ thống mới chỉ tích hợp Bộ luật Lao động 2019 và Luật Bảo hiểm xã hội 2024; chưa tích hợp Luật Việc làm (BHTN), Luật Bảo hiểm y tế và các Nghị định xử phạt vi phạm hành chính.
3. **Trải nghiệm chờ đợi trên CPU:** Mặc dù 23 giây là tốc độ nhanh cho mô hình ngôn ngữ chạy trên CPU, nhưng việc chưa có tính năng Streaming chữ chạy ra màn hình thời gian thực có thể tạo cảm giác chờ đợi cho người dùng.

---

### 3. Hướng phát triển trong tương lai
Để phát triển hệ thống thành một sản phẩm hoàn thiện phục vụ rộng rãi cộng đồng, các hướng nghiên cứu tiếp theo bao gồm:
1. **Mở rộng Cơ sở Tri thức:** Nạp thêm Luật Việc làm, Luật Bảo hiểm y tế, Luật An toàn vệ sinh lao động và các Nghị định hướng dẫn (Nghị định 145/2020/NĐ-CP, Nghị định 12/2022/NĐ-CP) vào ChromaDB.
2. **Hoàn thiện Bộ lọc Ranh giới:** Mở rộng từ điển từ khóa loại trừ cho `IntentAgent` và bổ sung ngưỡng lọc tương đồng ngữ nghĩa tối thiểu (Relevance Score Cutoff) cho `RetrievalAgent`.
3. **Cải thiện Giao diện và Trải nghiệm:** Tích hợp giao diện Streaming Tokens trên Streamlit để hiển thị câu trả lời ngay khi từng từ được sinh ra; bổ sung thanh tiến trình hiển thị trạng thái hoạt động của từng Agent.
4. **Nâng cấp Phần cứng và Mô hình:** Khi có điều kiện trang bị GPU chuyên dụng, nâng cấp mô hình lên các phiên bản 7B hoặc 14B tham số để nâng cao hơn nữa năng lực lập luận pháp lý chuyên sâu.

---

# TÀI LIỆU THAM KHẢO

1. **Quốc hội nước CHXHCN Việt Nam** (2019), *Bộ luật Lao động số 45/2019/QH14*, ban hành ngày 20/11/2019.
2. **Văn phòng Quốc hội** (2026), *Văn bản hợp nhất số 18/VBHN-VPQH - Bộ luật Lao động*, xác thực ngày 12/02/2026.
3. **Quốc hội nước CHXHCN Việt Nam** (2024), *Luật Bảo hiểm xã hội số 41/2024/QH15*, ban hành ngày 29/06/2024 (Có hiệu lực thi hành từ ngày 01/07/2025).
4. **Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I.** (2017), "Attention is all you need", *Advances in Neural Information Processing Systems (NeurIPS 2017)*, 30.
5. **Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D.** (2020), "Retrieval-augmented generation for knowledge-intensive NLP tasks", *Advances in Neural Information Processing Systems (NeurIPS 2020)*, 33, pp. 9459-9474.
6. **Robertson, S. E., Walker, S., Jones, S., Hancock-Beaulieu, M. M., & Gatford, M.** (1994), "Okapi at TREC-3", *Overview of the Third Text REtrieval Conference (TREC-3)*, pp. 109-126.
7. **Cormack, G. V., Clarke, C. L., & Buettcher, S.** (2009), "Reciprocal rank fusion outperforms condorcet and individual rank learning methods", *Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval*, pp. 758-759.
8. **Reimers, N., & Gurevych, I.** (2019), "Sentence-BERT: Sentence embeddings using Siamese BERT-networks", *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP 2019)*, pp. 3982-3992.
9. **Qwen Team** (2024), "Qwen2.5: A party of foundation and instruction-tuned large language models", *Alibaba Cloud Technical Report*, arXiv:2409.12191.
10. **Gerganov, G., et al.** (2023), "llama.cpp: Port of Facebook's LLaMA model in C/C++", *GitHub Repository*, https://github.com/ggerganov/llama.cpp.
