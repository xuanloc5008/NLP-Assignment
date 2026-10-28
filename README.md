# BÀI TẬP LỚN XỬ LÝ NGÔN NGỮ TỰ NHIÊN (CO3085)
## Đề tài: Trợ lý hỗ trợ học tập thông minh – Course Assistant
### Hướng tiếp cận: Classical / Statistical NLP

---

### 1. Thành viên nhóm & Phân chia công việc Phần 1 (Viết văn phạm và Parser)

| STT | Họ và Tên | Nhiệm vụ chính trong Phần 1 | File mã nguồn / Cấu hình | Output chịu trách nhiệm |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Đinh Hải Nam** | **Mục 3.1: Viết tập luật & Văn phạm CFG**<br>Xây dựng luật ngữ pháp miêu tả các câu hỏi thuộc miền môn học từ `entities.txt` và `sample_queries.txt`. | `models/grammar.cfg` | `output/grammar.txt` |
| 2 | **Thành Nhân** | **Mục 3.2: Viết giải thuật sinh câu**<br>Cài đặt thuật toán duyệt sinh tối đa 10.000 câu hợp lệ từ văn phạm CFG của Mục 3.1. | `src/generator.py` | `output/samples.txt` |
| 3 | **Đức Anh** | **Mục 3.3: Xây dựng bộ phân tích cú pháp (Parser)**<br>Dùng văn phạm phân tích các câu trong `input/sentences.txt`, xuất cây cú pháp hoặc `()`. | `src/parser.py` | `output/parse-results.txt` |
| 4 | **Xuân Lộc** | **Lead Integrator, Tokenizer & Test Pipeline**<br>Viết Tokenizer tiền xử lý từ ghép tiếng Việt, quản lý Repo, viết script điều phối và test tự động 3 file output. | `src/tokenizer.py`<br>`src/main_part1.py`<br>`src/main.py` | Toàn bộ pipeline & kiểm thử Docker |

---

### 2. Chi tiết phân công thực hiện Phần 1

```
                  ┌────────────────────────────────────────────────────────┐
                  │                XUÂN LỘC (Lead Integrator)              │
                  │  • Viết src/tokenizer.py (tách từ & gộp từ ghép '_')   │
                  │  • Viết src/main_part1.py điều phối chạy tự động       │
                  │  • Chạy kiểm thử nghiệm thu đủ 3 file output           │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                ┌─────────────────────────────┼────────────────────────────┐
                ▼                             ▼                            ▼
       [ĐINH HẢI NAM (3.1)]           [THÀNH NHÂN (3.2)]            [ĐỨC ANH (3.3)]
        Viết tập luật CFG            Thuật toán sinh câu             Bộ Parser Cú pháp
       models/grammar.cfg              src/generator.py                src/parser.py
               │                              │                              │
               ▼                              ▼                              ▼
       output/grammar.txt             output/samples.txt         output/parse-results.txt
```

#### Chi tiết công việc của từng người trong Phần 1:
1. **Đinh Hải Nam (Mục 3.1):**
   * **Nhiệm vụ:** Thiết kế tập luật Context-Free Grammar (CFG) cho tiếng Việt trong miền Course Assistant.
   * **Nội dung bao phủ:** Tối thiểu 7 nhóm câu hỏi: Thông tin môn học (`Q_COURSE_INFO`), Lịch học (`Q_SCHEDULE`), Chủ đề (`Q_TOPIC`), Bài tập (`Q_ASSIGNMENT`), Thời hạn (`Q_DEADLINE`), Tài liệu (`Q_RESOURCE`), Quy định (`Q_RULE`), Chuẩn đầu ra (`Q_LO`).
   * **File làm việc:** `models/grammar.cfg`.
   * **Output bàn giao:** `output/grammar.txt`.

2. **Thành Nhân (Mục 3.2):**
   * **Nhiệm vụ:** Lập trình giải thuật duyệt sinh câu tự động (BFS / DFS / NLTK generate) từ ký hiệu gốc `S` của văn phạm do Nam viết.
   * **Yêu cầu:** Mỗi dòng tương ứng một câu, câu sinh ra phải hợp lệ theo văn phạm, giới hạn tối đa **10.000 câu**.
   * **File làm việc:** `src/generator.py`.
   * **Output bàn giao:** `output/samples.txt`.

3. **Đức Anh (Mục 3.3):**
   * **Nhiệm vụ:** Xây dựng bộ phân tích cú pháp (Parser) sử dụng văn phạm CFG (khuyến nghị `nltk.ChartParser`).
   * **Yêu cầu:** Đọc `input/sentences.txt`. Với mỗi câu hợp lệ xuất chuỗi cây cú pháp chuẩn (ví dụ `(S (Q_SCHEDULE ...))`). Nếu câu không hợp lệ hoặc chứa từ ngoài từ điển (OOV), bắt buộc xuất đúng `()`.
   * **File làm việc:** `src/parser.py`.
   * **Output bàn giao:** `output/parse-results.txt`.

4. **Xuân Lộc (Lead Integrator):**
   * **Nhiệm vụ:** 
     * Viết `src/tokenizer.py` làm chuẩn chung tiền xử lý câu (lowercase, xoá dấu câu, gộp từ ghép tiếng Việt như `bài_tập_lớn`, `tín_chỉ`) làm cầu nối giữa Nam và Đức Anh.
     * Viết `src/main_part1.py` để chạy một lệnh duy nhất kết nối code của Nam, Nhân, Đức Anh.
     * Kiểm tra định dạng 3 file output và thiết lập môi trường Docker.

---

### 3. Hướng dẫn cài đặt
Hệ thống phát triển trên nền tảng Python (>= 3.8 / 3.10).

**Cài đặt môi trường:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 4. Hướng dẫn chạy chương trình

#### 4.1. Lệnh chạy độc lập cho từng thành viên (Kiểm tra output riêng)
Mỗi thành viên có thể chạy riêng mã nguồn của mình để kiểm tra file output tương ứng:

| Thành viên | Lệnh chạy tại thư mục `project/` | File output tự kiểm tra | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Đinh Hải Nam (3.1)** | `cp models/grammar.cfg output/grammar.txt` | `output/grammar.txt` | Xuất tập luật văn phạm CFG |
| **Thành Nhân (3.2)** | `python3 -m src.generator` | `output/samples.txt` | Sinh tối đa 10.000 câu mẫu |
| **Đức Anh (3.3)** | `python3 -m src.parser` | `output/parse-results.txt` | Phân tích cú pháp `sentences.txt` |
| **Xuân Lộc (Tokenizer)** | `python3 -m src.tokenizer` | Console output | Kiểm tra tách từ & gộp từ ghép |

#### 4.2. Lệnh chạy tổng hợp Phần I (Xuân Lộc tổng hợp)
Sau khi các thành viên hoàn thành hoặc cập nhật code mới, chạy 1 lệnh duy nhất để tự động xuất **cả 3 file output của Phần I**:
```bash
python3 -m src.main_part1
```
*Kết quả sinh ra đủ 3 file:*
* `output/grammar.txt` (từ Nam)
* `output/samples.txt` (từ Nhân)
* `output/parse-results.txt` (từ Đức Anh)

#### 4.3. Lệnh chạy toàn bộ hệ thống (End-to-End Pipeline)
Chạy toàn bộ pipeline từ Phần I đến Phần IV:
```bash
python3 -m src.main
```

#### 4.4. Chạy kiểm thử qua Docker (Môi trường chấm bài của giảng viên)
```bash
docker build -t course-assistant .
docker run --rm -v $(pwd)/input:/nlp/input -v $(pwd)/output:/nlp/output course-assistant
```

---

### 5. Mô tả kiến trúc hệ thống
Hệ thống tuân thủ chuỗi xử lý tuần tự (Pipeline) của Classical NLP:
```
Natural Language Input (Câu hỏi tự nhiên)
       │
       ▼
Vietnamese Tokenizer (Tiền xử lý & Chuẩn hoá từ ghép tiếng Việt - Lộc)
       │
       ▼
Syntactic Parser (Phân tích cú pháp dựa trên CFG - Nam & Đức Anh)
       │
       ▼
Semantic Representation (Biểu diễn ngữ nghĩa vị từ / Logic)
       │
       ▼
Intent & Entity Recognition (Xác định ý định & Trích xuất thực thể)
       │
       ▼
Knowledge Base Query Engine (Truy vấn dữ liệu môn học có cấu trúc)
       │
       ▼
Natural Language Generation (Sinh câu trả lời tự nhiên + Fallback xử lý out-of-scope)
```

---

### 6. Mô tả Grammar (Văn phạm - Mục 3.1)
- Văn phạm được thiết kế dưới dạng **Context-Free Grammar (CFG)** trong file `models/grammar.cfg` và xuất ra `output/grammar.txt`.
- Gồm ký hiệu xuất phát `S` phân rã thành các nhóm Intent chính:
  - `Q_COURSE_INFO`: Hỏi thông tin chung (tín chỉ, thời lượng thi).
  - `Q_SCHEDULE`: Hỏi lịch học các tuần, kế hoạch 15 tuần.
  - `Q_TOPIC`: Hỏi về các chủ đề kiến thức (CFG, Parsing, Semantics, Ambiguity...).
  - `Q_ASSIGNMENT` & `Q_DEADLINE`: Hỏi bài tập lớn và thời hạn nộp.
  - `Q_RESOURCE`: Hỏi tài liệu học tập, giáo trình tham khảo.
  - `Q_RULE`: Hỏi quy định học phần, chính sách sử dụng AI/LLM.
  - `Q_LO`: Hỏi về các chuẩn đầu ra (Learning Outcomes).

---

### 7. Mô tả Parser (Mục 3.3)
- Sử dụng thuật toán phân tích cú pháp **Chart Parser** (Bottom-Up Chart Parsing).
- Đầu vào: Đọc danh sách câu từ file `input/sentences.txt`.
- Đầu ra: Xuất cấu trúc cây cú pháp dạng chuỗi ngoặc mở/đóng vào `output/parse-results.txt`.
- Xử lý câu không hợp lệ: Nếu câu chứa từ vựng ngoài miền (OOV) hoặc cấu trúc không khớp luật văn phạm, parser tự động xuất cặp ngoặc đơn rỗng `()`.

---

### 8. Mô tả Semantic Representation
- Ánh xạ câu sau khi phân tích cú pháp sang biểu diễn logic dạng Frame / Predicate:
  - `GET_CREDIT(course=CO3085)`
  - `GET_SCHEDULE(week=3)`
  - `GET_TOPIC(chapter=CH04)`
- Kết quả được ghi nhận vào `output/semantic.txt`.

---

### 9. Mô tả phương pháp xử lý Intent/Entity
- **Intent Identification:** Kết hợp giữa cấu trúc nhãn cây cú pháp (Grammar-driven) và mô hình phân loại học máy thống kê (TF-IDF + Linear Classifier).
- **Entity Extraction:** Sử dụng Trie / Regex pattern matching dựa trên từ điển thực thể `entities.txt` để trích xuất các slot (`course`, `week`, `chapter`, `assignment_part`, `topic`).
- Kết quả xuất ra `output/intent-entity.txt`.

---

### 10. Mô tả Knowledge Base và cách truy vấn
- Dữ liệu môn học từ `data/` (`course_info.txt`, `schedule.txt`, `topics.txt`, `assignments.txt`, `regulations.txt`) được phân tích và lập chỉ mục trong bộ nhớ.
- Query Engine chuyển `(Intent, Entity)` thành khóa tra cứu trực tiếp trong Knowledge Base.
- Kết quả truy vấn được ghi nhận vào `output/query.txt` và chuyển tiếp cho bộ sinh câu trả lời `output/answer.txt`.

---

### 11. Mô tả lựa chọn Classical/Statistical NLP
- Hệ thống áp dụng nghiêm ngặt các phương pháp NLP cổ điển và thống kê, không sử dụng LLM hay API sinh văn bản tự do ở tầng xử lý lõi.
- Đảm bảo tính minh bạch, khả năng giải thích rõ ràng của từng bước trong pipeline và tốc độ xử lý nhanh.

---

### 12. Mô tả cách đánh giá & Các hạn chế của hệ thống
- **Cách đánh giá:** Đánh giá trên tập dữ liệu kiểm thử gồm câu hợp lệ, biến thể cách diễn đạt (paraphrase), câu ngoài phạm vi (out-of-scope), câu thiếu thông tin. Báo cáo số liệu và phân tích lỗi được xuất ra `output/evaluation.txt`.
- **Hạn chế:** Phụ thuộc vào độ bao phủ của tập luật CFG; từ vựng ngoài từ điển (OOV) sẽ trả về `()` hoặc fallback; chưa tối ưu cho các câu sai lỗi chính tả phức tạp.
