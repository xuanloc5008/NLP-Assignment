# Mục 4.1.3 – 4.1.5: Knowledge Base, Query & Sinh câu trả lời (NLG)

**Phụ trách:** Đức Anh
**File mã nguồn:** `src/knowledge_base.py`, `src/query_engine.py`, `src/nlg.py`
**Dữ liệu:** `data/*.txt`
**Input:** `input/sentences.txt`
**Output:** `output/query.txt`, `output/answer.txt` (dòng N của mỗi file ứng với câu N của input)

---

## 1. Cách chạy

```bash
# Chạy riêng Mục 4.1.3 - 4.1.5 (không cần nltk)
python3 -m src.nlg

# Hoặc chạy toàn bộ pipeline
python3 -m src.main
```

Kết quả in ra console: `-> Đã trả lời 31/34 câu (còn lại fallback), ghi vào .../query.txt và .../answer.txt`
(3 câu fallback là 3 câu ngoài phạm vi Q026–Q028.)

---

## 2. Kiến trúc

```
(intent, entities, câu gốc)
        │
        ▼
QueryEngine.normalize_entities ──► chuẩn hoá slot ('Chương 4' -> CH04, 'L.O.2.5' -> LO2.5, ...)
        │                          + đọc thêm slot từ câu gốc nếu bộ nhận diện bỏ sót
        ▼
QueryEngine.plan ────────────────► {table, select, where}   (intent UNKNOWN -> None)
        │
        ├──► build_query ─────────► output/query.txt   "SELECT week FROM schedule WHERE chapter = 'CH04'"
        │
        ▼
QueryEngine.execute_query ───────► dict kết quả trên KnowledgeBase, hoặc None
        │                          (None -> thử FAQ theo độ trùng từ, ngưỡng Jaccard 0.75)
        ▼
AnswerGenerator (template) ──────► output/answer.txt   hoặc câu Fallback chuẩn
```

---

## 3. Các thành phần

### 3.1. `KnowledgeBase` (`src/knowledge_base.py`) – Mục 4.1.3

Đọc các file bán cấu trúc trong `data/` và lập chỉ mục thành dict tra cứu theo khoá:

| Bảng | Nguồn | Khoá | Nội dung |
|---|---|---|---|
| `course_info` | `course_info.txt` | tên thuộc tính | tín chỉ, ECTS, giờ học, tỉ lệ đánh giá, midterm/final, các phần chính |
| `los` | `course_info.txt` | `LO2.5` | mô tả chuẩn đầu ra (LO1..LO4 và LO chi tiết) |
| `schedule` | `schedule.txt` | `WEEK_03` | chương, phần, chủ đề, activity, milestone của từng tuần |
| `topics` | `topics.txt` | `CH04` | tiêu đề, keywords, summary, subtopics, **các tuần học** (liên kết từ schedule) |
| `assignments` | `assignments.txt` | `BTL01`, `PART_I`..`PART_IV` | mục tiêu, yêu cầu, output gợi ý của từng phần |
| `regulations` | `regulations.txt` | `AI_USAGE`, `LLM_RAG`, ... | nội dung quy định |
| `resources` | `resources.txt` | `TEXTBOOK_1`, `REFERENCE_2`, ... | tiêu đề, tác giả, năm, mục đích sử dụng |
| `faq` | `faq.txt` | – | cặp câu hỏi / trả lời (dùng dự phòng) |
| `lexicon` | `entities.txt` (mục TOPICS) | `CFG`, `SEMANTIC_GRAMMAR`, ... | từ đồng nghĩa Anh–Việt của chủ đề |

`LO_CHAPTERS` ánh xạ LO chi tiết sang chương theo đề cương (vd `LO2.5 -> CH06`), dùng cho câu "Nội dung này nằm ở chương nào?".

### 3.2. `QueryEngine` (`src/query_engine.py`) – Mục 4.1.3 + 4.1.4

- `build_query(intent, entities, sentence="")` → câu truy vấn dạng SQL-like (ghi vào `query.txt`); câu ngoài miền ra `NO_QUERY -- intent=UNKNOWN (ngoài phạm vi)`.
- `execute_query(intent, entities, sentence="")` → dict kết quả cho NLG hoặc `None`.
- Tìm chủ đề → chương xếp hạng theo vị trí xuất hiện: keywords (3) > tiêu đề (2) > subtopic/summary (1), chỉ giữ các chương điểm cao nhất (vd PCFG → Chương 3 và Chương 6). So khớp **nguyên cụm từ** để `cfg` không khớp nhầm vào `pcfg`.
- Câu hỏi có/không (`... có ... không?`) được kiểm chứng trên nội dung KB: trả lời "Có" kèm bằng chứng, hoặc "Không" khi dữ liệu không đề cập.
- Thuộc tính của `GET_COURSE_INFO` (tín chỉ, phần, midterm, giờ học, đánh giá...) được xác định từ từ khoá trong câu, hoặc slot `attribute` nếu bộ nhận diện cung cấp.
- Intent `CONTEXT_DEPENDENT` (sau khi Phần III đã giải tham chiếu thành entity): tự suy ra intent từ loại slot (`chapter` → GET_TOPIC, `assignment_part` → GET_ASSIGNMENT, `lo` → GET_LO...).

### 3.3. `AnswerGenerator` (`src/nlg.py`) – Mục 4.1.4 + 4.1.5

- Template-based NLG: mỗi loại kết quả (`week`, `topic_chapters`, `chapter_check`, `exam`, `part_outputs`, `rule`, `resources`...) có một hàm template `_t_<type>`.
- **Fallback** trả về đúng câu chuẩn `"Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."` khi:
  - intent `UNKNOWN` / ngoài phạm vi (Q026–Q028);
  - entity không tồn tại trong KB (vd "Chương 20", "Tuần 20", tài liệu về chủ đề không có);
  - KB không có dữ liệu cho intent (vd `GET_INSTRUCTOR` – dữ liệu không có thông tin giảng viên).
- Hệ thống **không tự tạo thông tin**: mọi câu trả lời đều lấy từ `data/`.

---

## 4. Giao diện với các module khác

**Schema entity mà QueryEngine nhận** (giá trị có thể là mã chuẩn hoặc dạng tự nhiên, sẽ được chuẩn hoá):

| Slot | Ví dụ giá trị |
|---|---|
| `course` | `CO3085`, `NLP` |
| `week` | `WEEK_03`, `Tuần 3`, `3` |
| `chapter` | `CH04`, `Chương 4`, `4` |
| `topic` | `CFG`, `SEMANTIC_GRAMMAR`, `semantic grammar`, `hỏi đáp` |
| `lo` | `LO2.5`, `L.O.2.5` |
| `assignment` / `assignment_part` | `BTL01` / `PART_I`, `Phần I` |
| `rule_topic` | `AI_USAGE`, `LLM_RAG` |
| `exam` | `MIDTERM`, `FINAL` |
| `resource_topic` | `STATISTICAL_NLP`, `Python NLP` |

Nhãn phẳng như trong `sample_queries.txt` (`CH04`, `WEEK_03`, `PART_I`...) đổi sang dict bằng `label_to_entities(label)`.

- **Thành Nhân (4.1.2):** `IntentEntityDetector.detect(sentence)` chỉ cần trả `(intent, dict)` theo schema trên. Khi detector còn trả `UNKNOWN`, `make_detector()` tạm dùng nhãn kỳ vọng trong `data/sample_queries.txt` để Mục 4.1.3–4.1.5 kiểm thử được độc lập; detector nhận diện được câu nào thì kết quả của detector được ưu tiên cho câu đó.
- **Xuân Lộc (Phần III):** sau khi giải tham chiếu ("chương này" → `CH03`, "chương sau" → `CH12`), gọi `nlg.generate_answer("CONTEXT_DEPENDENT" hoặc intent, entities_đã_giải, sentence)`. Với `{}` (chưa giải được) hệ thống trả fallback.
- **Xuân Lộc (Phần IV):** dùng `qe.execute_query(...)` / `nlg.generate_answer(...)` để tính QA accuracy.
- `src/main.py`: đã nối bước ghi `query.txt` và `answer.txt` vào pipeline.

---

## 5. Kết quả trên `input/sentences.txt`

| Câu | Query | Câu trả lời |
|---|---|---|
| Môn NLP có bao nhiêu tín chỉ? | `SELECT credits FROM course_info WHERE course_id = 'CO3085'` | Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ. |
| Chương 4 học vào tuần nào? | `SELECT week FROM schedule WHERE chapter = 'CH04'` | Chương 4 – Features and Augmented Grammar được học vào tuần 4 và tuần 5. |
| PCFG được học ở đâu? | `SELECT chapter_id FROM topics WHERE topic LIKE '%PCFG%'` | PCFG (...) được trình bày trong Chương 3 – Grammar and Parsing và Chương 6 – ... |
| Nó có liên quan đến parsing không? *(CH04)* | `SELECT contains FROM topics WHERE chapter_id = 'CH04' AND text CONTAINS 'PARSING'` | Có. Chương 4 – Features and Augmented Grammar có đề cập đến parsing, cụ thể: Parsing with features. |
| Phần này cần xuất file gì? *(PART_I)* | `SELECT outputs FROM assignments WHERE assignment_id = 'BTL01' AND part = 'PART_I'` | Phần I (Grammar and Parser) cần xuất các file: output/grammar.txt, output/samples.txt và output/parse-results.txt. |
| Ai là tổng thống của Pháp? | `NO_QUERY -- intent=UNKNOWN (ngoài phạm vi)` | Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học. |

Toàn bộ 34 dòng xem tại `output/query.txt` và `output/answer.txt`.
