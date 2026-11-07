# BÀI TẬP LỚN XỬ LÝ NGÔN NGỮ TỰ NHIÊN (CO3085)
## Đề tài: Trợ lý hỗ trợ học tập thông minh – Course Assistant
### Hướng tiếp cận: Classical / Statistical NLP

---

### 1. Thành viên nhóm & Phân chia công việc

#### 1.1. Phần I: Viết văn phạm và Parser (ĐÃ HOÀN THÀNH 100%)
| STT | Họ và Tên | Nhiệm vụ chính trong Phần 1 | File mã nguồn / Cấu hình | Output chịu trách nhiệm | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | **Đinh Hải Nam** | **Mục 3.1: Viết tập luật & Văn phạm CFG**<br>Xây dựng luật CFG miêu tả các câu hỏi từ `entities.txt` và `sample_queries.txt`. | `models/grammar.cfg` | `output/grammar.txt` | **HOÀN THÀNH** |
| 2 | **Thành Nhân** | **Mục 3.2: Viết giải thuật sinh câu**<br>Cài đặt thuật toán duyệt sinh tối đa 10.000 câu hợp lệ từ văn phạm CFG. | `src/generator.py` | `output/samples.txt` | **HOÀN THÀNH** |
| 3 | **Đức Anh** | **Mục 3.3: Xây dựng bộ phân tích cú pháp (Parser)**<br>Dùng Chart Parser phân tích `input/sentences.txt`, xuất cây cú pháp hoặc `()`. | `src/parser.py` | `output/parse-results.txt` | **HOÀN THÀNH** |
| 4 | **Xuân Lộc** | **Lead Integrator, Tokenizer & Test Pipeline**<br>Viết Tokenizer tiền xử lý từ ghép tiếng Việt, gộp code các nhánh và viết script kiểm thử tự động. | `src/tokenizer.py`<br>`src/grammar_loader.py`<br>`src/main_part1.py` | Toàn bộ pipeline Phần I | **HOÀN THÀNH** |

#### 1.2. Phần II, III & IV: Diễn giải ngữ nghĩa, Hội thoại & Đánh giá (Kế hoạch thực hiện tiếp theo)
| STT | Họ và Tên | Nhiệm vụ chính trong Phần 2, 3, 4 | File mã nguồn phụ trách | Output chịu trách nhiệm |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Đinh Hải Nam** | **Mục 4.1.1: Xây dựng biểu diễn ngữ nghĩa (Semantic Representation)**<br>Ánh xạ cây cú pháp / câu sang biểu diễn vị từ/logic (`GET_CREDIT(...)`, `GET_SCHEDULE(...)`, `GET_TOPIC(...)`...). | `src/semantic.py` | `output/semantic.txt` |
| 2 | **Thành Nhân** | **Mục 4.1.2: Nhận diện Intent & Trích xuất Entity**<br>Nhận diện 8 loại ý định và trích xuất thực thể theo Lexicon chuẩn từ `entities.txt` (dùng rule matching hoặc TF-IDF/ML). | `src/intent_entity.py` | `output/intent-entity.txt` |
| 3 | **Đức Anh** | **Mục 4.1.3 + 4.1.4 + 4.1.5: Knowledge Base, Query & Sinh câu trả lời (NLG)**<br>Đọc và chỉ mục hoá `data/*.txt`; chuyển (Intent, Entity) thành câu truy vấn; sinh câu trả lời tự nhiên dạng template và xử lý fallback cho câu ngoài phạm vi. | `src/knowledge_base.py`<br>`src/query_engine.py`<br>`src/nlg.py` | `output/query.txt`<br>`output/answer.txt` |
| 4 | **Xuân Lộc** | **Phần III (Ngữ cảnh hội thoại) & Phần IV (Đánh giá) + Lead Integrator**<br>Quản lý State Memory xử lý đại từ tham chiếu ("nó", "phần này", "chương sau"); xây dựng test suite tính Accuracy và phân tích lỗi; ráp nối toàn bộ pipeline. | `src/dialogue.py`<br>`src/evaluator.py`<br>`src/main.py` | `output/dialogue.txt`<br>`output/evaluation.txt` |

---

### 2. Sơ đồ luồng xử lý toàn hệ thống (End-to-End Pipeline)

```
[Câu hỏi người dùng]
        │
        ▼
[Tokenizer - Xuân Lộc] ───────────────► Chuẩn hoá Unicode, tách từ, gộp từ ghép
        │
        ▼
[Parser - Đức Anh & Hải Nam] ─────────► Cây cú pháp hoặc () (Mục 3.1 & 3.3)
        │
        ▼
[Semantic - Hải Nam] ────────────────► Biểu diễn vị từ logic (Mục 4.1.1)
        │
        ▼
[Intent/Entity - Thành Nhân] ─────────► Nhận diện Intent & trích xuất Slots (Mục 4.1.2)
        │
        ▼
[Query Engine & KB - Đức Anh] ────────► Truy vấn Knowledge Base nội bộ (Mục 4.1.3)
        │
        ▼
[NLG & Fallback - Đức Anh] ───────────► Sinh câu trả lời tự nhiên hoặc Fallback (Mục 4.1.4 & 4.1.5)
        │
        ├─────────────────────────────► [Dialogue Context - Xuân Lộc] (Phần III)
        │
        └─────────────────────────────► [Evaluation Suite - Xuân Lộc] (Phần IV)
```

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

#### 4.1. Chạy kiểm thử độc lập Phần I
Mỗi thành viên có thể chạy riêng mã nguồn của mình để kiểm tra file output tương ứng:

| Thành viên | Lệnh chạy tại thư mục `project/` | File output tự kiểm tra | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Đinh Hải Nam (3.1)** | `cp models/grammar.cfg output/grammar.txt` | `output/grammar.txt` | Xuất tập luật văn phạm CFG |
| **Thành Nhân (3.2)** | `python3 -m src.generator` | `output/samples.txt` | Sinh tối đa 10.000 câu mẫu |
| **Đức Anh (3.3)** | `python3 -m src.parser` | `output/parse-results.txt` | Phân tích cú pháp `sentences.txt` |
| **Xuân Lộc (Tổng hợp)** | `python3 -m src.main_part1` | Cả 3 file output trên | Tự động chạy và kiểm định format 3.1, 3.2, 3.3 |

#### 4.2. Chạy kiểm thử độc lập Phần II, III, IV
| Thành viên | Lệnh chạy tại thư mục `project/` | File output tự kiểm tra | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Đinh Hải Nam (4.1.1)** | `python3 -m src.semantic` | `output/semantic.txt` | Xuất biểu diễn ngữ nghĩa dạng vị từ |
| **Thành Nhân (4.1.2)** | `python3 -m src.intent_entity` | `output/intent-entity.txt` | Xuất Intent & Entity trích xuất |
| **Đức Anh (4.1.3 - 4.1.5)** | `python3 -m src.nlg` | `output/query.txt`<br>`output/answer.txt` | Xuất câu truy vấn KB và câu trả lời |
| **Xuân Lộc (Phần III & IV)** | `python3 -m src.dialogue`<br>`python3 -m src.evaluator` | `output/dialogue.txt`<br>`output/evaluation.txt` | Xử lý hội thoại & Báo cáo đánh giá |

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

### 5. Mô tả chi tiết các thành phần hệ thống

#### 5.1. Văn phạm (Grammar - Mục 3.1)
- Văn phạm được thiết kế dưới dạng **Context-Free Grammar (CFG)** trong file `models/grammar.cfg` và xuất ra `output/grammar.txt`.
- Gồm ký hiệu xuất phát `S` phân rã thành các nhóm Intent chính:
  - `Q_COURSE_INFO`: Hỏi thông tin chung (tín chỉ, thời lượng thi).
  - `Q_SCHEDULE`: Hỏi lịch học các tuần, kế hoạch 15 tuần.
  - `Q_TOPIC`: Hỏi về các chủ đề kiến thức (CFG, Parsing, Semantics, Ambiguity...).
  - `Q_ASSIGNMENT` & `Q_DEADLINE`: Hỏi bài tập lớn và thời hạn nộp.
  - `Q_RESOURCE`: Hỏi tài liệu học tập, giáo trình tham khảo.
  - `Q_RULE`: Hỏi quy định học phần, chính sách sử dụng AI/LLM.
  - `Q_LO`: Hỏi về các chuẩn đầu ra (Learning Outcomes).
  - `Q_CONTEXT`: Hỏi câu có hiện tượng tham chiếu / tỉnh lược.

#### 5.2. Parser cú pháp (Mục 3.3)
- Sử dụng thuật toán **Bottom-Up Chart Parser** (`nltk.ChartParser`).
- Hỗ trợ gộp từ ghép theo chiến lược Longest Match dựa trên tập terminal của văn phạm.
- Nếu câu hợp lệ: xuất cây cú pháp dạng chuỗi ngoặc mở/đóng trên 1 dòng.
- Nếu câu không hợp lệ hoặc chứa từ ngoài từ điển (OOV): xuất cặp ngoặc đơn rỗng `()`.

#### 5.3. Semantic Representation (Mục 4.1.1)
- Ánh xạ câu sang biểu diễn logic dạng Frame / Predicate:
  - `GET_CREDIT(course=CO3085)`
  - `GET_SCHEDULE(week=WEEK_03)`
  - `GET_TOPIC(chapter=CH04)`
  - `GET_DEADLINE(assignment=PROJECT)`

#### 5.4. Intent & Entity (Mục 4.1.2)
- Xác định 8 nhóm Intent và các Slot Entity liên quan (course, week, chapter, assignment_part, topic, lo, rule_topic).

#### 5.5. Knowledge Base & Query Engine (Mục 4.1.3 - 4.1.5)
- Dữ liệu môn học trong `data/` được lập chỉ mục có cấu trúc.
- Chuyển `(Intent, Entity)` thành truy vấn lấy thông tin chính xác.
- Sinh câu trả lời tự nhiên bằng mẫu câu (Template-based NLG).
- Cơ chế Fallback an toàn: Với câu ngoài phạm vi hoặc không tìm thấy dữ liệu, xuất đúng câu thông báo chuẩn:
  > *"Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."*

#### 5.6. Ngữ cảnh hội thoại cục bộ (Phần III)
- Lưu trữ State Memory từ lượt tương tác trước.
- Giải quyết đại từ thay thế (*"nó"*, *"chương này"*, *"phần này"*, *"còn chương sau?"*, *"nội dung này"*).

#### 5.7. Đánh giá hệ thống (Phần IV)
- Đánh giá trên tập `sample_queries.txt` đo lường Intent Accuracy, QA Accuracy, phân tích nguyên nhân lỗi và đánh giá ưu/nhược điểm của phương pháp Classical NLP.
