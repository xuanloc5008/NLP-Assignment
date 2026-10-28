# BÀI TẬP LỚN XỬ LÝ NGÔN NGỮ TỰ NHIÊN (CO3085)
## Đề tài: Trợ lý hỗ trợ học tập thông minh – Course Assistant
### Hướng tiếp cận: Classical / Statistical NLP

---

### 1. Thành viên nhóm
| STT | Họ và Tên | MSSV | Vai trò chính |
| :---: | :--- | :---: | :--- |
| 1 | Nguyễn Văn A | 201xxxx | Phụ trách Phần I (Grammar & Tokenizer) |
| 2 | Trần Thị B | 201xxxx | Phụ trách Phần I (Giải thuật sinh câu) & Phần II (Intent/Entity) |
| 3 | Lê Văn C | 201xxxx | Phụ trách Phần I (Parser cú pháp) & Phần II (KB & NLG) |
| 4 | Phạm Minh D | 201xxxx | Lead Integrator, Phần III (Discourse), Phần IV (Đánh giá) & DevOps |

---

### 2. Hướng dẫn cài đặt
Hệ thống phát triển trên nền tảng Python (>= 3.8 / 3.10).

**Cài đặt qua môi trường ảo (venv):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Hướng dẫn chạy chương trình

**Cách 1: Chạy trực tiếp qua Python**
```bash
# Chạy toàn bộ hệ thống
python3 -m src.main

# Hoặc chạy riêng Phần I (Grammar, Generation, Parser)
python3 -m src.main_part1
```

**Cách 2: Chạy kiểm thử qua Docker (Môi trường chấm bài)**
```bash
docker build -t course-assistant .
docker run --rm -v $(pwd)/input:/nlp/input -v $(pwd)/output:/nlp/output course-assistant
```

---

### 4. Mô tả kiến trúc hệ thống
Hệ thống tuân thủ chuỗi xử lý tuần tự (Pipeline) của NLP truyền thống:
```
Natural Language Input (Câu hỏi tự nhiên)
       │
       ▼
Vietnamese Tokenizer (Tiền xử lý & Chuẩn hoá từ ghép)
       │
       ▼
Syntactic Parser (Bộ phân tích cú pháp Chart Parser dựa trên CFG)
       │
       ▼
Semantic Representation (Biểu diễn ngữ nghĩa vị từ / Logic)
       │
       ▼
Intent & Entity Recognition (Xác định mục đích & Thực thể liên quan)
       │
       ▼
Knowledge Base Query Engine (Truy vấn dữ liệu môn học có cấu trúc)
       │
       ▼
Natural Language Generation (Sinh câu trả lời tự nhiên + Fallback xử lý out-of-scope)
```

---

### 5. Mô tả Grammar (Văn phạm)
- Văn phạm được thiết kế dưới dạng **Context-Free Grammar (CFG)** trong file `models/grammar.cfg` và xuất ra `output/grammar.txt`.
- Gồm ký hiệu xuất phát `S` phân rã thành các nhóm Intent chính:
  - `Q_COURSE_INFO`: Hỏi thông tin chung (tín chỉ, thời lượng thi).
  - `Q_SCHEDULE`: Hỏi lịch học các tuần, kế hoạch 15 tuần.
  - `Q_TOPIC`: Hỏi về các chủ đề kiến thức (CFG, Parsing, Semantics, Ambiguity...).
  - `Q_ASSIGNMENT` & `Q_DEADLINE`: Hỏi bài tập lớn và thời hạn nộp.
  - `Q_RESOURCE`: Hỏi tài liệu học tập, giáo trình tham khảo.
  - `Q_RULE`: Hỏi quy định học phần, chính sách sử dụng AI/LLM.
- Từ điển từ vựng (Terminals) được tích hợp dựa trên bảng thực thể môn học.

---

### 6. Mô tả Parser
- Sử dụng thuật toán phân tích cú pháp **Chart Parser** (Bottom-Up Chart Parsing).
- Đầu vào: Đọc danh sách câu từ file `input/sentences.txt`.
- Đầu ra: Xuất cấu trúc cây cú pháp dạng chuỗi ngoặc mở/đóng vào `output/parse-results.txt`.
- Xử lý câu không hợp lệ: Nếu câu chứa từ vựng ngoài miền (OOV) hoặc cấu trúc không khớp luật văn phạm, parser tự động xuất cặp ngoặc đơn rỗng `()`.

---

### 7. Mô tả Semantic Representation
- Ánh xạ câu sau khi phân tích cú pháp sang biểu diễn logic dạng Frame / Predicate:
  - `GET_CREDIT(course=CO3085)`
  - `GET_SCHEDULE(week=3)`
  - `GET_TOPIC(chapter=CH04)`
- Kết quả được ghi nhận vào `output/semantic.txt`.

---

### 8. Mô tả phương pháp xử lý Intent/Entity
- **Intent Identification:** Kết hợp giữa cấu trúc nhãn cây cú pháp (Grammar-driven) và mô hình phân loại học máy thống kê (TF-IDF + Linear Classifier).
- **Entity Extraction:** Sử dụng Trie / Regex pattern matching dựa trên từ điển thực thể `entities.txt` để trích xuất các slot (`course`, `week`, `chapter`, `assignment_part`, `topic`).
- Kết quả xuất ra `output/intent-entity.txt`.

---

### 9. Mô tả Knowledge Base và cách truy vấn
- Dữ liệu môn học từ `data/` (`course_info.txt`, `schedule.txt`, `topics.txt`, `assignments.txt`, `regulations.txt`) được phân tích và lập chỉ mục trong bộ nhớ.
- Query Engine chuyển `(Intent, Entity)` thành khóa tra cứu trực tiếp trong Knowledge Base.
- Kết quả truy vấn được ghi nhận vào `output/query.txt` và chuyển tiếp cho bộ sinh câu trả lời `output/answer.txt`.

---

### 10. Mô tả lựa chọn Classical/Statistical NLP
- Hệ thống áp dụng nghiêm ngặt các phương pháp NLP cổ điển và thống kê, không sử dụng LLM hay API sinh văn bản tự do ở tầng xử lý lõi.
- Đảm bảo tính minh bạch, khả năng giải thích rõ ràng của từng bước trong pipeline và tốc độ xử lý nhanh.

---

### 11. Mô tả cách đánh giá
- Đánh giá trên tập dữ liệu kiểm thử bao gồm các nhóm: câu hợp lệ, biến thể cách diễn đạt (paraphrase), câu ngoài phạm vi (out-of-scope), câu thiếu thông tin.
- Các chỉ số đánh giá: Parsing Accuracy, Intent Accuracy, Entity F1-score, End-to-End QA Accuracy.
- Báo cáo số liệu và phân tích nguyên nhân lỗi được xuất ra `output/evaluation.txt`.

---

### 12. Các hạn chế của hệ thống
- Phụ thuộc vào tập luật văn phạm: các câu có trật tự từ quá khác biệt hoặc từ ngữ địa phương có thể không parse được.
- Từ vựng nằm ngoài từ điển (OOV) sẽ bị trả về `()` hoặc chuyển sang cơ chế fallback.
- Cần tiếp tục bổ sung thêm các luật mở rộng cho câu ghép phức tạp.
