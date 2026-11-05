# BỘ CÂU HỎI VÀ TRẢ LỜI BẢO VỆ ĐỒ ÁN TOÀN DIỆN (PROJECT DEFENSE Q&A)
## HỆ THỐNG AGENTIC AI LEGAL CHATBOT

---

> **Mục đích:** Tài liệu luyện tập bảo vệ đồ án tốt nghiệp dành cho sinh viên. Bao gồm hơn 40 câu hỏi thường gặp của Hội đồng giám khảo kèm câu trả lời mẫu ngắn gọn, dễ hiểu, tự tin và phần gợi ý phản xạ *"Nếu giảng viên hỏi tiếp..."*.

---

## MỤC LỤC 10 CHỦ ĐỀ

1. [Nhóm 1: Kiến thức AI và Tổng quan Dự án (Câu 1 - 4)](#nhóm-1-kiến-thức-ai-và-tổng-quan-dự-án)
2. [Nhóm 2: Mô hình Ngôn ngữ Lớn (LLM) và Hugging Face (Câu 5 - 8)](#nhóm-2-mô-hình-ngôn-ngữ-lớn-llm-và-hugging-face)
3. [Nhóm 3: Kỹ thuật RAG và Mô hình Embedding (Câu 9 - 12)](#nhóm-3-kỹ-thuật-rag-và-mô-hình-embedding)
4. [Nhóm 4: Tìm kiếm Lai (Hybrid Search), BM25 và RRF (Câu 13 - 17)](#nhóm-4-tìm-kiếm-lai-hybrid-search-bm25-và-rrf)
5. [Nhóm 5: Kiến trúc Đa tác tử (Agentic AI Multi-Agent) (Câu 18 - 22)](#nhóm-5-kiến-trúc-đa-tác-tử-agentic-ai-multi-agent)
6. [Nhóm 6: Lập luận Pháp lý Fact-to-Law và FactExtractor (Câu 23 - 26)](#nhóm-6-lập-luận-pháp-lý-fact-to-law-và-factextractor)
7. [Nhóm 7: Kiểm định Chống Ảo giác (Validation & Hallucination) (Câu 27 - 30)](#nhóm-7-kiểm-định-chống-ảo-giác-validation--hallucination)
8. [Nhóm 8: Dữ liệu và Cơ sở Tri thức Knowledge Base (Câu 31 - 34)](#nhóm-8-dữ-liệu-và-cơ-sở-tri-thức-knowledge-base)
9. [Nhóm 9: Đo lường Hiệu năng, Độ trễ và Bộ nhớ RAM (Câu 35 - 38)](#nhóm-9-đo-lường-hiệu-năng-độ-trễ-và-bộ-nhớ-ram)
10. [Nhóm 10: Đánh giá Rủi ro, Giới hạn và Hướng phát triển (Câu 39 - 42)](#nhóm-10-đánh-giá-rủi-ro-giới-hạn-và-hướng-phát-triển)

---

### NHÓM 1: KIẾN THỨC AI VÀ TỔNG QUAN DỰ ÁN

#### Câu 1: Em hãy trình bày ngắn gọn mục tiêu của đề tài này là gì?
- **Trả lời mẫu:**  
  *"Thưa thầy cô, mục tiêu của đề tài là xây dựng một hệ thống Chatbot chuyên sâu hỗ trợ tra cứu và tư vấn pháp luật Lao động và Bảo hiểm xã hội Việt Nam. Hệ thống được thiết kế theo kiến trúc Agentic RAG (Tạo sinh có tăng cường truy xuất kết hợp đa tác tử), có khả năng vận hành hoàn toàn cục bộ, độc lập ngoại tuyến (Local/Offline) trên máy tính cá nhân mà không phụ thuộc vào Internet hay các API thương mại bên ngoài."*
- **Nếu giảng viên hỏi tiếp:** *"Tại sao em lại chọn đề tài này thay vì dùng luôn ChatGPT?"*  
  $\rightarrow$ *"Thưa thầy cô, ChatGPT dùng chung rất dễ gặp hiện tượng 'ảo giác' (bịa đặt điều luật) và không cập nhật được các luật mới của Việt Nam như Luật BHXH 2024. Hơn nữa, trong tư vấn pháp lý, dữ liệu doanh nghiệp cần bảo mật tuyệt đối, việc chạy offline 100% trên máy tính giúp thông tin không bao giờ bị lộ ra ngoài."*

#### Câu 2: Sự khác biệt lớn nhất giữa Chatbot thông thường và Chatbot của em là gì?
- **Trả lời mẫu:**  
  *"Chatbot thông thường hoạt động theo từ khóa cứng hoặc cây quyết định (If-Else), khi người dùng hỏi khác đi một từ là hệ thống chịu thua. Còn hệ thống của em hiểu được ngôn ngữ tự nhiên, có khả năng ánh xạ tiếng lóng đời thường (như 'nghỉ đẻ', 'bị đuổi việc') vào đúng thuật ngữ pháp lý ('thai sản', 'sa thải') và tự động tìm chính xác văn bản luật để suy luận ra câu trả lời."*

#### Câu 3: Đầu vào và đầu ra của hệ thống hoạt động như thế nào?
- **Trả lời mẫu:**  
  *"Đầu vào là câu hỏi văn bản tiếng Việt tự nhiên của người dùng. Đầu ra là một văn bản tư vấn có cấu trúc chuẩn mực gồm 4 phần: 1. Kết luận trực diện; 2. Căn cứ pháp lý trích dẫn rõ số Điều, Khoản, số trang; 3. Giải thích điều kiện áp dụng; 4. Các lưu ý về thời điểm hiệu lực và ngoại lệ."*

#### Câu 4: Vì sao hệ thống không sử dụng các dịch vụ Cloud như OpenAI hay Gemini?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, có 3 lý do chính: Thứ nhất là tính bảo mật (nhiều câu hỏi về tranh chấp lao động, tiền lương chứa thông tin nhạy cảm của người lao động và doanh nghiệp). Thứ hai là tính sẵn sàng (hệ thống có thể hoạt động ở vùng sâu vùng xa hoặc môi trường mạng cô lập không có Internet). Thứ ba là chi phí vận hành (hệ thống chạy vĩnh viễn trên máy tính nội bộ mà không tốn phí thuê bao token API hàng tháng)."*

---

### NHÓM 2: MÔ HÌNH NGÔN NGỮ LỚN (LLM) VÀ HUGGING FACE

#### Câu 5: Hệ thống của em đang sử dụng mô hình LLM nào? Tại sao lại chọn nó?
- **Trả lời mẫu:**  
  *"Hệ thống sử dụng mô hình **Qwen2.5-1.5B-Instruct**, định dạng lượng tử hóa **GGUF Q4_K_M**. Em chọn mô hình này vì nó có 1.5 tỷ tham số, dung lượng chỉ khoảng 1.1 GB, vừa vặn để chạy mượt mà trên CPU Intel Core i5 và 16 GB RAM. Quan trọng hơn, dòng mô hình Qwen2.5 hỗ trợ tiếng Việt cực kỳ xuất sắc và có tư duy lập luận logic rất tốt trong phân khúc mô hình nhỏ dưới 3 tỷ tham số."*
- **Nếu giảng viên hỏi tiếp:** *"Tại sao em không dùng mô hình 7B hay 14B cho thông minh hơn?"*  
  $\rightarrow$ *"Dạ, mô hình 7B cần tối thiểu 6-8 GB RAM chỉ riêng cho model và suy luận trên CPU sẽ mất từ 1.5 đến 2 phút cho một câu hỏi, gây nghẽn toàn bộ hệ thống. Với bài toán RAG, khi ngữ cảnh luật đã được RetrievalAgent lọc sạch và đưa vào, mô hình 1.5B đã đủ sức suy luận chính xác mà thời gian chỉ mất khoảng 20-30 giây."*

#### Câu 6: Định dạng GGUF và kỹ thuật Quantization (Lượng tử hóa) là gì?
- **Trả lời mẫu:**  
  *"Dạ, Quantization là kỹ thuật nén các con số trọng số của mô hình từ số thực 16-bit (FP16) xuống dạng số nguyên 4-bit (INT4). Nhờ đó dung lượng mô hình giảm đi 4 lần và lượng RAM chiếm dụng giảm từ 4 GB xuống còn khoảng 1.1 GB. GGUF là định dạng tệp chuẩn hiện đại nhất được tối ưu riêng để chạy mô hình nén này trực tiếp trên CPU thông qua thư viện llama.cpp."*

#### Câu 7: Vai trò của thư viện llama.cpp và llama-cpp-python là gì?
- **Trả lời mẫu:**  
  *"llama.cpp là một thư viện viết bằng C++ thuần túy, được tối ưu hóa các tập lệnh phần cứng của CPU (như AVX2) để tính toán ma trận với tốc độ cao nhất. Còn `llama-cpp-python` là gói thư viện đóng vai trò cầu nối, giúp mã nguồn Python của dự án có thể gọi và điều khiển trực tiếp nhân suy luận C++ đó một cách mượt mà."*

#### Câu 8: Hugging Face đóng vai trò gì trong dự án của em?
- **Trả lời mẫu:**  
  *"Hugging Face đóng vai trò là kho lưu trữ mã nguồn mở, nơi em tải các trọng số mô hình Embedding và LLM ban đầu về. Sau khi đã tải về thư mục cache cục bộ, hệ thống được thiết lập chế độ `local_files_only = True` để vận hành hoàn toàn offline, không bao giờ kết nối lại tới Hugging Face trong quá trình hoạt động."*

---

### NHÓM 3: KỸ THUẬT RAG VÀ MÔ HÌNH EMBEDDING

#### Câu 9: Em hiểu RAG là gì? Tại sao không dùng Fine-tuning (huấn luyện bổ sung) cho LLM?
- **Trả lời mẫu:**  
  *"RAG là kỹ thuật 'tìm tài liệu trước, trả lời sau'. Em không chọn Fine-tuning vì 3 lý do: Thứ nhất, Fine-tuning rất tốn kém tài nguyên máy tính (cần GPU đắt tiền). Thứ hai, Fine-tuning không thể loại bỏ hoàn toàn hiện tượng ảo giác và không thể trích dẫn chính xác số trang/văn bản. Thứ ba, khi luật thay đổi (như có Luật BHXH mới), với RAG em chỉ cần cập nhật file văn bản trong CSDL là xong ngay lập tức trong vài giây, còn Fine-tuning sẽ phải đào tạo lại toàn bộ mô hình từ đầu."*

#### Câu 10: Embedding là gì? Nó biến đổi câu văn như thế nào?
- **Trả lời mẫu:**  
  *"Embedding là quá trình dùng một mạng nơ-ron để chuyển đổi một đoạn văn bản thành một danh sách các con số (gọi là vector toán học). Trong dự án của em, mỗi đoạn luật được biến thành một vector gồm **384 con số**. Điểm mấu chốt là các câu văn có ý nghĩa tương đồng nhau trong đời thực thì các vector của chúng sẽ nằm rất gần nhau trong không gian đa chiều."*

#### Câu 11: Mô hình Embedding trong dự án là gì? Kết quả A/B Test giữa V1 và V2 ra sao?
- **Trả lời mẫu:**  
  *"Ban đầu ở Phase 3, hệ thống dùng `all-MiniLM-L6-v2` (tiếng Anh). Đến Phase 4.2, qua kiểm nghiệm A/B Testing, em đã nâng cấp lên mô hình đa ngôn ngữ `paraphrase-multilingual-MiniLM-L12-v2`. Kết quả thực nghiệm đo trên 16 câu hỏi benchmark cho thấy: Tỷ lệ tìm đúng Điều luật (Hit@5) tăng vọt từ **43.75% lên 81.25%** (gấp gần 2 lần) và tìm đúng Khoản luật tăng từ **18.75% lên 56.25%** (gấp 3 lần)."*

#### Câu 12: ChromaDB là gì và nó lưu trữ những gì?
- **Trả lời mẫu:**  
  *"ChromaDB là một hệ quản trị cơ sở dữ liệu vector mã nguồn mở chạy cục bộ. Nó lưu trữ 1.296 vector 384 chiều tương ứng với 1.296 đoạn luật cùng các thông tin siêu dữ liệu (metadata) như tên luật, số hiệu, số trang và ngày hiệu lực. Khi có câu hỏi, ChromaDB sẽ tính toán khoảng cách Cosine để tìm ra các vector gần nhất."*

---

### NHÓM 4: TÌM KIẾM LAI (HYBRID SEARCH), BM25 VÀ RRF

#### Câu 13: Tại sao phải dùng Tìm kiếm lai (Hybrid Search) mà không dùng riêng Dense hay BM25?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, vì 2 phương pháp này bù trừ hoàn hảo cho nhau:  
  - **Dense Search (Vector):** Rất giỏi hiểu ngữ nghĩa và từ đồng nghĩa (người dùng gõ 'nghỉ đẻ' vẫn tìm ra 'thai sản'), nhưng lại rất kém khi tìm số hiệu chính xác như 'Điều 102' hay các từ chuyên ngành hiếm.  
  - **BM25:** Rất giỏi bắt chính xác từng chữ cái, mã hiệu văn bản, nhưng lại mù tịt về ngữ nghĩa nếu người dùng dùng từ khác đi.  
  Kết hợp cả hai lại thành Hybrid Search giúp hệ thống vừa hiểu được ý nghĩa câu hỏi, vừa không bao giờ bị trượt số hiệu điều luật."*

#### Câu 14: Thuật toán BM25 hoạt động ra sao? N-gram trong Phase 4.1 giúp ích gì?
- **Trả lời mẫu:**  
  *"BM25 dựa trên tần suất từ (TF) và độ hiếm của từ trong toàn bộ tài liệu (IDF). Những từ phổ biến ở đâu cũng có sẽ bị hạ điểm, chỉ từ khóa hiếm mới được điểm cao. Ở Phase 4.1, em đã cải tiến bộ tách từ sang dạng N-gram với từ điển từ ghép pháp luật tiếng Việt. Thay vì tách rời 'hợp', 'đồng', 'lao', 'động', hệ thống gom thành cụm 'hợp đồng lao động', giúp độ chính xác của BM25 tăng thêm hơn 35%."*

#### Câu 15: Thuật toán Reciprocal Rank Fusion (RRF) hoạt động như thế nào?
- **Trả lời mẫu:**  
  *"RRF là công thức gộp 2 danh sách kết quả dựa trên thứ hạng: $\text{Điểm} = \sum \frac{w}{k + \text{rank}}$. Trong đó em đặt $k = 60$ theo chuẩn tối ưu. Nếu một điều luật vừa đứng top đầu bên BM25, vừa đứng top đầu bên Dense, nó sẽ nhận điểm RRF cao nhất và được chọn vào Top-K để gửi cho LLM."*

#### Câu 16: Kỹ thuật Parent-Child Retrieval (Truy xuất Cha - Con) là gì?
- **Trả lời mẫu:**  
  *"Trong văn bản luật, các quy định thường nằm rải rác: Khoản 1 nêu nguyên tắc chung, nhưng Khoản 2, Khoản 3 lại nêu các trường hợp ngoại lệ hoặc mức phạt. Nếu công cụ tìm kiếm chỉ lấy được Khoản 1 thì LLM sẽ bị thiếu ngữ cảnh. Kỹ thuật Parent-Child của em giải quyết việc này bằng cách: khi tìm trúng một Khoản (Child), hệ thống tự động bốc trọn vẹn cả Điều luật chứa nó (Parent) để gửi cho LLM đọc."*

#### Câu 17: Candidate Pool và Top-K khác nhau thế nào?
- **Trả lời mẫu:**  
  *"Candidate Pool là số tài liệu sơ tuyển mà BM25 và Dense bốc về ban đầu (em đặt là 15 tài liệu mỗi bên). Sau khi đưa 30 tài liệu này qua bộ chấm điểm RRF, hệ thống chỉ lọc lấy ra **Top-K = 4** tài liệu xuất sắc nhất để gửi vào prompt cho LLM, tránh làm loãng ngữ cảnh."*

---

### NHÓM 5: KIẾN TRÚC ĐA TÁC TỬ (AGENTIC AI MULTI-AGENT)

#### Câu 18: Hệ thống của em có bao nhiêu Agent? Kể tên và nêu nhiệm vụ từng Agent?
- **Trả lời mẫu:**  
  *"Hệ thống gồm 5 Agent chức năng được điều phối bởi `LegalAgentOrchestrator`:  
  1. `IntentAgent`: Phân loại câu hỏi (lao động, BHXH hay ngoài phạm vi) và mở rộng từ đồng nghĩa.  
  2. `RetrievalAgent`: Tìm kiếm lai BM25 + Dense và mở rộng Parent-Child.  
  3. `LegalAnalysisAgent`: Bóc tách dữ kiện thực tế và suy luận Tam đoạn luận bằng Local LLM.  
  4. `ValidationAgent`: Thanh tra độc lập kiểm tra trích dẫn ma và số liệu không căn cứ.  
  5. `ResponseAgent`: Đóng gói câu trả lời thành văn bản Markdown 4 phần chuẩn công vụ."*

#### Câu 19: `ConversationMemory` và `QueryRewriter` hoạt động thế nào trong chat nhiều lượt?
- **Trả lời mẫu:**  
  *"Dạ, `ConversationMemory` quản lý lịch sử theo từng phiên làm việc (Session) riêng biệt để không bị nhớ nhầm giữa các người dùng. Khi người dùng hỏi câu tiếp nối như: 'Hết thời gian đó công ty không báo kết quả thì sao?', `QueryRewriter` sẽ tự động phát hiện chữ 'đó' thay thế cho 'thời gian thử việc' ở câu trước, và viết lại thành câu hoàn chỉnh độc lập trước khi gửi cho RetrievalAgent tìm kiếm."*

#### Câu 20: Điều gì xảy ra khi người dùng hỏi một câu ngoài phạm vi (Out-of-Scope)?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, `IntentAgent` sẽ phát hiện ngay các từ khóa ngoài phạm vi (như 'vượt đèn đỏ', 'ly hôn', 'trộm cắp') và kích hoạt cơ chế ngắt sớm (Fast Exit). Toàn bộ hệ thống dừng lại ngay lập tức, không tốn tài nguyên tìm kiếm hay gọi LLM, và `ResponseAgent` sẽ xuất bản lời từ chối lịch sự trong chưa đầy 1 mili-giây."*

#### Câu 21: Vòng lặp thử lại có giới hạn (Bounded Retry Loop) trong Orchestrator là gì?
- **Trả lời mẫu:**  
  *"Nếu sau khi LLM phân tích xong mà `ValidationAgent` báo câu trả lời chưa đạt hoặc thiếu căn cứ, Orchestrator sẽ kích hoạt cơ chế Retry duy nhất 1 lần (`MAX_RETRY_ATTEMPTS = 1`). Hệ thống tự động mở rộng vùng tìm kiếm (`Top-K + 2` và `Candidate Pool + 10`) để tìm thêm tài liệu. Nếu vẫn không tìm thấy, hệ thống sẽ dừng lại và thông báo chưa đủ căn cứ chứ không thử lại vô hạn để tránh treo máy."*

#### Câu 22: Tại sao em không gộp toàn bộ các bước vào 1 Agent duy nhất cho đơn giản?
- **Trả lời mẫu:**  
  *"Việc gộp chung (Monolithic prompt) sẽ khiến một LLM nhỏ như 1.5B bị quá tải: vừa phải tìm kiếm, vừa phải suy luận, vừa phải tự kiểm tra. Bằng cách chia nhỏ thành các Agent chuyên biệt theo nguyên tắc đơn nhiệm (Single Responsibility Principle), mỗi Agent làm xuất sắc một phần việc, và quan trọng nhất là có `ValidationAgent` độc lập đứng sau kiểm soát, loại bỏ hoàn toàn nguy cơ bịa đặt thông tin."*

---

### NHÓM 6: LẬP LUẬN PHÁP LÝ FACT-TO-LAW VÀ FACTEXTRACTOR

#### Câu 23: Lập luận Fact-to-Law theo Tam đoạn luận (Syllogism) trong dự án là gì?
- **Trả lời mẫu:**  
  *"Đây là phương pháp tư duy pháp lý kinh điển:  
  - **Đại tiền đề:** Quy định của điều luật (Luật quy định nợ lương được nghỉ việc ngay).  
  - **Tiểu tiền đề:** Sự việc thực tế của người dùng (Tôi bị công ty nợ lương 2 tháng).  
  - **Kết luận:** Áp dụng luật vào sự việc để đưa ra quyền lợi hợp pháp (Bạn được quyền nghỉ việc ngay).  
  Hệ thống ép LLM phải suy luận tuần tự theo 3 bước này để đảm bảo câu trả lời luôn có căn cứ pháp lý vững chắc."*

#### Câu 24: `FactExtractor` làm nhiệm vụ gì trước khi gọi LLM?
- **Trả lời mẫu:**  
  *"Dạ, `FactExtractor` sử dụng các biểu thức chính quy Regex tốc độ cao để bóc tách câu hỏi người dùng thành một hồ sơ dữ kiện gồm: Chủ thể (NLĐ hay NSDLĐ), Sự kiện (sa thải, nợ lương, thai sản), Số liệu (2 tháng, 60 ngày), và đặc biệt là chỉ ra **những dữ kiện còn thiếu** (như chưa rõ loại hợp đồng lao động nào) để nhắc nhở người dùng."*

#### Câu 25: Hệ thống xử lý thế nào đối với mốc thời gian chuyển tiếp của Luật Bảo hiểm xã hội 2024?
- **Trả lời mẫu:**  
  *"Dạ, Luật BHXH 2024 số 41/2024/QH15 có hiệu lực từ ngày 01/07/2025. `FactExtractor` có cơ chế Temporal Reasoning (Suy luận thời gian): Khi phát hiện sự việc xảy ra từ tháng 07/2025 trở đi (ví dụ người dùng hỏi sinh con tháng 8/2025), hệ thống sẽ tự động kích hoạt văn bản luật mới và chèn thêm ghi chú hiệu lực chính thức vào câu trả lời."*

#### Câu 26: Nếu người dùng đặt câu hỏi quá mơ hồ, hệ thống sẽ xử lý thế nào?
- **Trả lời mẫu:**  
  *"Hệ thống sẽ không tự ý phỏng đoán để kết luận vội vã. `FactExtractor` và `LegalAnalysisAgent` sẽ nhận diện dữ kiện thiếu và đưa ra câu trả lời có tính phân nhánh điều kiện hoặc yêu cầu người dùng cung cấp thêm thông tin cụ thể (ví dụ: cần nêu rõ hình thức nghỉ việc là gì thì mới tính được chế độ)."*

---

### NHÓM 7: KIỂM ĐỊNH CHỐNG ẢO GIÁC (VALIDATION & HALLUCINATION)

#### Câu 27: Trích dẫn ma (Hallucinated Citations) là gì và hệ thống chặn nó ra sao?
- **Trả lời mẫu:**  
  *"Trích dẫn ma là hiện tượng LLM tự bịa ra số Điều hoặc tên Luật không có thật trên đời. `ValidationAgent` chặn việc này bằng cách quét toàn bộ văn bản câu trả lời, rút ra tất cả các điều luật được nhắc tới và đối chiếu thẳng vào danh mục 1.296 chunks trong cơ sở dữ liệu. Nếu điều luật đó không tồn tại, nó lập tức bị gạch bỏ và cảnh báo."*

#### Câu 28: Unsupported Numbers (Số liệu không căn cứ) là gì?
- **Trả lời mẫu:**  
  *"Là các con số định lượng (như tỷ lệ %, số ngày, số tiền) xuất hiện trong câu trả lời của LLM nhưng không hề có mặt trong đoạn luật được trích dẫn làm căn cứ. `ValidationAgent` sẽ so khớp chéo và phát cờ cảnh báo người dùng ngay lập tức."*

#### Câu 29: Tỷ lệ trích dẫn ma trong đợt nghiệm thu Phase 4.3.1 của dự án là bao nhiêu?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, tỷ lệ trích dẫn ma đạt **0% (0 / 42 trường hợp)**. Toàn bộ các Điều, Khoản mà hệ thống đưa ra đều tồn tại chính xác trong Bộ luật Lao động 18/VBHN-VPQH hoặc Luật Bảo hiểm xã hội 41/2024/QH15."*

#### Câu 30: Tại sao em không dùng chính LLM để kiểm tra lại câu trả lời của nó?
- **Trả lời mẫu:**  
  *"Dạ, việc dùng LLM để tự chấm điểm LLM (LLM-as-a-judge) tiềm ẩn rủi ro rất lớn vì bản thân LLM khi thẩm định lại có thể tiếp tục bị ảo giác hoặc đồng tình với câu trả lời sai của chính nó. Do đó, em sử dụng `ValidationAgent` bằng mã nguồn Python và Regex thuần túy để tạo ra một **chốt chặn thanh tra hoàn toàn khách quan, có tính xác định 100% (Deterministic Guardrail)**."*

---

### NHÓM 8: DỮ LIỆU VÀ CƠ SỞ TRI THỨC KNOWLEDGE BASE

#### Câu 31: Cơ sở dữ liệu hiện tại của hệ thống gồm những văn bản nào? Bao nhiêu chunks?
- **Trả lời mẫu:**  
  *"Dạ, Knowledge Base hiện gồm 2 văn bản pháp luật chính thức:  
  1. Bộ luật Lao động số 18/VBHN-VPQH (gốc là Luật số 45/2019/QH14).  
  2. Luật Bảo hiểm xã hội số 41/2024/QH15 (hiệu lực từ 01/07/2025).  
  Tổng cộng được bóc tách thành **1.296 chunks** bao quát toàn bộ **363 điều luật**."*

#### Câu 32: Chiến lược chia nhỏ văn bản (Chunking Strategy) của em có gì đặc biệt?
- **Trả lời mẫu:**  
  *"Dạ, em không cắt văn bản theo số lượng từ ngẫu nhiên (Fixed-size chunking) như RAG thông thường vì sẽ làm đứt gãy câu chữ pháp lý. Thay vào đó, em cắt theo cấu trúc ngữ nghĩa văn bản quy phạm pháp luật: Mỗi Điều luật là một Parent, mỗi Khoản là một Child chunk độc lập. Nhờ đó, mỗi chunk đều mang ý nghĩa pháp lý trọn vẹn kèm số trang gốc."*

#### Câu 33: Những văn bản pháp luật quan trọng nào CHƯA có trong hệ thống?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, hệ thống hiện CHƯA có: Luật Việc làm (quy định về Bảo hiểm thất nghiệp), Luật Bảo hiểm y tế, Luật Thuế thu nhập cá nhân, và các Nghị định xử phạt vi phạm hành chính (Nghị định 12/2022). Đây là ranh giới dữ liệu rõ ràng của đề tài."*

#### Câu 34: Khi người dùng hỏi một nội dung chưa có trong CSDL (như Bảo hiểm thất nghiệp), hệ thống phản ứng thế nào?
- **Trả lời mẫu:**  
  *"Trong đợt audit Phase 4.3.1 vừa qua, khi hỏi về BHTN, hệ thống trích xuất Điều 168 BLLĐ về trách nhiệm tham gia bảo hiểm, và hoàn toàn không bịa đặt ra số tháng hưởng. Tuy nhiên, nhóm cũng phát hiện hạn chế là hệ thống chưa phát ra câu từ chối dứt khoát rằng BHTN thuộc Luật Việc làm. Nhóm đã đề xuất giải pháp bổ sung từ khóa loại trừ tại `IntentAgent` để chặn đứng vấn đề này trong tương lai."*

---

### NHÓM 9: ĐO LƯỜNG HIỆU NĂNG, ĐỘ TRỄ VÀ BỘ NHỚ RAM

#### Câu 35: Thời gian xử lý trung bình một câu hỏi là bao lâu? Bước nào chiếm nhiều thời gian nhất?
- **Trả lời mẫu:**  
  *"Dạ, thời gian xử lý trung bình toàn trình là **23.50 giây / câu hỏi**. Trong đó:  
  - Khâu tìm kiếm tài liệu (Retrieval): Chỉ mất **0.05 giây (53.8 ms)**.  
  - Khâu kiểm tra (Validation): Chỉ mất **0.002 giây (2.3 ms)**.  
  - Khâu suy luận sinh chữ của Local LLM trên CPU: Chiếm **23.44 giây (hơn 99.7% tổng thời gian)**."*

#### Câu 36: Tại sao thời gian sinh chữ của LLM lại mất hơn 20 giây? Có cách nào tối ưu hơn không?
- **Trả lời mẫu:**  
  *"Dạ, vì hệ thống chạy hoàn toàn ngoại tuyến trên CPU Intel Core i5 máy tính cá nhân (không có card màn hình GPU chuyên dụng). CPU phải tính toán tuần tự từng token với 6 luồng xử lý. Tốc độ sinh chữ đạt khoảng 10-12 tokens/giây, một câu trả lời 250-300 chữ mất khoảng 20-25 giây là đặc tính vật lý bình thường. Để tối ưu trải nghiệm, giải pháp tốt nhất là tích hợp cơ chế Streaming (chữ chạy ra đến đâu hiện đến đó) để người dùng không cảm thấy phải chờ đợi."*

#### Câu 37: Hệ thống tiêu thụ bao nhiêu RAM? Có bị hiện tượng tràn hay rò rỉ bộ nhớ (Memory Leak) không?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, qua đo đạc liên tục trên 15 đến 42 câu hỏi bằng thư viện `psutil`:  
  - RAM ban đầu: 458 MB.  
  - RAM sau nạp mô hình: 1.921 MB.  
  - RAM đỉnh: **2.388 MB (~2.33 GB)**, chiếm khoảng 14.5% tổng RAM 16 GB của máy tính.  
  - Dung lượng RAM duy trì ổn định quanh mức 2.3 GB trong suốt quá trình chạy và được bộ thu gom rác Python tự động giải phóng. Hệ thống **hoàn toàn không có hiện tượng rò rỉ bộ nhớ (Zero Memory Leak)**."*

#### Câu 38: Kết quả thử nghiệm hồi quy (Regression Testing) 10 câu hỏi tiêu biểu đạt kết quả ra sao?
- **Trả lời mẫu:**  
  *"Dạ, 10 câu hỏi hồi quy bao quát các chủ đề quan trọng từ thử việc, nghỉ phép, làm thêm giờ, chấm dứt HĐLĐ đến thai sản, ốm đau đều vượt qua kiểm định an toàn với trạng thái PASSED hoặc WARNING kiểm soát được. Câu hỏi ngoài phạm vi về luật giao thông được từ chối ngay lập tức trong 0.00 giây mà không tốn tài nguyên."*

---

### NHÓM 10: ĐÁNH GIÁ RỦI RO, GIỚI HẠN VÀ HƯỚNG PHÁT TRIỂN

#### Câu 39: Đợt kiểm toán ngoài phạm vi (Out-of-Scope Audit) vừa qua đạt tỷ lệ bao nhiêu? Có phát hiện lỗi gì nghiêm trọng không?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, đợt kiểm toán trên 42 câu hỏi đạt tỷ lệ an toàn **80.95% (34/42 câu PASS)**. Nhóm đã phát hiện ra 4 lỗi nghiêm trọng tập trung ở nhóm câu hỏi về **Thuế thu nhập cá nhân** và **Bảo hiểm thất nghiệp** (ví dụ câu 'Lương 30 triệu đóng thuế gì'). Nguyên nhân là do có từ 'lương', `IntentAgent` bị nhầm là luật lao động và Retrieval bốc Điều 102 BLLĐ về khấu trừ lương, khiến LLM suy đoán sai lệch rằng lương 30 triệu không đóng thuế."*

#### Câu 40: Nhóm đã đề xuất giải pháp tối thiểu nào để khắc phục các lỗi ranh giới trên?
- **Trả lời mẫu:**  
  *"Dạ, nhóm đã thiết kế giải pháp 3 lớp mà hoàn toàn không cần sửa cấu trúc mô hình:  
  1. Thêm các từ khóa 'thuế tncn', 'bảo hiểm y tế', 'bảo hiểm thất nghiệp' vào danh sách từ khóa ngoài phạm vi (`OUT_OF_SCOPE_KEYWORDS`) của `IntentAgent` để chặn ngay từ vòng ngoài (< 1ms).  
  2. Bổ sung luật cấm trong prompt: Cấm dùng Điều 102 BLLĐ để giải thích cho vấn đề thuế.  
  3. Bổ sung luật kiểm định trong `ValidationAgent`: Nếu câu hỏi có chữ thuế mà căn cứ là Điều 102 thì lập tức đánh FAILED."*

#### Câu 41: Theo em, rủi ro lớn nhất khi đưa hệ thống này vào thực tế là gì?
- **Trả lời mẫu:**  
  *"Dạ, rủi ro lớn nhất là người dùng tin tưởng tuyệt đối vào kết luận của AI cho các tình huống pháp lý phức tạp ngoài đời (vốn cần luật sư xem xét hồ sơ, hợp đồng gốc và các yếu tố chứng cứ). Vì vậy, hệ thống luôn bắt buộc phải có câu từ chối trách nhiệm pháp lý (Disclaimer) và khuyến nghị người dùng đối chiếu lại với mục Căn cứ pháp lý (số Điều, số trang) được trích dẫn cụ thể trước khi thực hiện hành vi pháp lý."*

#### Câu 42: Nếu có thêm thời gian và kinh phí, em sẽ phát triển hệ thống này theo hướng nào tiếp theo?
- **Trả lời mẫu:**  
  *"Dạ thưa thầy cô, em sẽ tập trung vào 3 hướng:  
  1. Mở rộng cơ sở tri thức: Bổ sung thêm Luật Việc làm (BHTN), Luật Bảo hiểm y tế và các Nghị định hướng dẫn xử phạt vào ChromaDB.  
  2. Tối ưu trải nghiệm: Bổ sung cơ chế Streaming Token và thanh tiến trình trạng thái từng Agent trên giao diện Web Streamlit.  
  3. Nâng cấp mô hình: Thử nghiệm các mô hình ngôn ngữ tiếng Việt 3B hoặc 7B khi hệ thống được trang bị phần cứng có GPU tăng tốc."*

---
*Tài liệu được biên soạn phục vụ công tác chuẩn bị bảo vệ đồ án tốt nghiệp – Chúc bạn bảo vệ thành công rực rỡ!*
