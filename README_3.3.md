# Mục 3.3 – Bộ phân tích cú pháp (Parser)

**Phụ trách:** Đức Anh
**File mã nguồn:** `src/parser.py`
**Văn phạm sử dụng:** `models/grammar.cfg`
**Input:** `input/sentences.txt` (mỗi dòng một câu)
**Output:** `output/parse-results.txt` (mỗi dòng một cây cú pháp, hoặc `()` nếu câu không thuộc văn phạm)

---

## 1. Cách chạy

```bash
pip install -r requirements.txt

# Chạy riêng Mục 3.3
python3 -m src.parser

# Hoặc chạy cả Phần I (3.1 + 3.2 + 3.3)
python3 -m src.main_part1
```

Kết quả in ra console: `-> Đã phân tích 31/34 câu hợp lệ, ghi vào .../output/parse-results.txt`

---

## 2. Các lỗi văn phạm đã sửa trong `models/grammar.cfg`

| # | Vị trí | Lỗi | Hậu quả | Cách sửa |
|---|---|---|---|---|
| 1 | Luật `TOPIC_VI` (dòng 94) | Dòng `TOPIC_VI -> ... \| 'gán_nhãn_từ_loại'` thiếu dấu nối dòng `\`, dòng kế tiếp lại bắt đầu bằng `\|` | `nltk.CFG.fromstring` báo `ValueError: Expected a nonterminal`, **không nạp được văn phạm**, nên cả parser lẫn generator đều không chạy | Thêm `\` vào cuối dòng 94 |
| 2 | Ký hiệu gốc `S` (dòng 7) | `S` không có `Q_LO` và `Q_CONTEXT`, dù hai luật này đã được định nghĩa | Các câu hỏi chuẩn đầu ra (`L.O.2.5 là gì?`) và các câu có đồng tham chiếu (`Nó có liên quan đến parsing không?`, `Còn chương sau?`, `Phần này cần xuất file gì?`) đều bị trả về `()` | `S -> ... \| Q_RULE \| Q_LO \| Q_CONTEXT` |
| 3 | Luật `TOPIC_EN` (dòng 93) | Terminal `'word sense disambiguation'` chứa khoảng trắng | Tokenizer tách câu theo khoảng trắng nên token này không bao giờ được tạo ra, dẫn đến terminal "chết" | Đổi thành `'word_sense_disambiguation'` (dạng từ ghép nối `_`, nhất quán với các terminal khác) |

> `output/grammar.txt` được sao chép lại từ `models/grammar.cfg` khi chạy `src.main_part1`, nên hai file luôn giống nhau.

---

## 3. Những gì đã thực hiện

### 3.1. Kiến trúc

```
câu thô ──► tokenize ──► kiểm tra OOV ──► nltk.ChartParser ──► cây đầu tiên ──► chuỗi ngoặc 1 dòng
                              │ có từ ngoài từ vựng      │ không có cây
                              └────────────► "()" ◄──────┘
```

### 3.2. Lớp `CourseParser` (`src/parser.py`)

| Phương thức | Chức năng |
|---|---|
| `__init__(grammar_path)` | Đọc văn phạm (chuẩn hoá Unicode NFC), tạo `nltk.CFG` và `nltk.ChartParser`. Trích **tập terminal** để kiểm tra OOV và **bảng từ ghép** (mọi terminal có `_`, ví dụ `bài_tập_lớn` ứng với `("bài","tập","lớn")`) |
| `tokenize(sentence)` | Tiền xử lý câu cho khớp với terminal của văn phạm (chi tiết ở mục 3.3 bên dưới) |
| `parse_tree(sentence)` | Trả về `nltk.Tree` đầu tiên, hoặc `None` nếu câu rỗng, có từ OOV hoặc không có cây phân tích |
| `parse_sentence(sentence)` | Trả về chuỗi cây trên **một dòng** (`tree.pformat(margin=sys.maxsize)`), hoặc `()` |
| `process_file(input, output)` | Đọc file UTF-8 và ghi **đúng 1 dòng output cho mỗi dòng input** (kể cả dòng trống), để dòng N của output luôn ứng với câu N của input |

Giao diện `CourseParser(grammar_path).process_file(in, out)` được giữ nguyên như khung ban đầu, nên `src/main_part1.py` và `src/main.py` không cần sửa.

### 3.3. Tiền xử lý / tách từ

1. Chuẩn hoá Unicode **NFC** (tránh lệch giữa tiếng Việt dựng sẵn và tổ hợp) và chuyển về chữ thường.
2. Chuẩn hoá mã chuẩn đầu ra: `L.O.2.5`, `LO 2.5` thành `lo2.5`.
3. `/` đổi thành khoảng trắng (`LLM/RAG` thành `llm rag`).
4. Bỏ dấu câu `? ! , ; : " ' ( ) …` và dấu `.` ở đầu/cuối token. Dấu `.` bên trong token (`lo2.5`, `tp.hcm`) được giữ lại.
5. **Gộp từ ghép theo chiến lược khớp dài nhất (longest match)**, dựa trên bảng từ ghép lấy **trực tiếp từ văn phạm**. Ví dụ:
   - `bài tập lớn` thành `bài_tập_lớn`
   - `semantic grammar` thành `semantic_grammar`
   - `llm rag` thành `llm_rag`
   - `môn học gồm` thành `môn_học gồm`, còn `môn nlp` vẫn giữ `môn`

   Nhờ vậy, khi Nam bổ sung từ ghép mới vào `grammar.cfg`, parser tự nhận ra mà không phải sửa code.

### 3.4. Xử lý câu không hợp lệ

- Câu rỗng hoặc chỉ có khoảng trắng: `()`
- Có token không thuộc từ vựng văn phạm (OOV): `()`. Việc kiểm tra này chạy trước khi parse, vì NLTK sẽ ném `ValueError` nếu gặp từ lạ.
- Mọi từ đều thuộc từ vựng nhưng sai cấu trúc (ví dụ `gì học 3 tuần`): ChartParser không tìm được cây nên trả `()`.
- Câu nhập nhằng (nhiều cây): lấy cây đầu tiên. Với bộ 34 câu hiện tại, mỗi câu hợp lệ chỉ có đúng **1 cây**.

---

## 4. Kết quả kiểm thử

### 4.1. Bộ `input/sentences.txt` (34 câu, trùng với Q001–Q034 trong `data/sample_queries.txt`): **34/34 PASSED**

31 câu trong miền đều có cây cú pháp đúng nhóm luật; 3 câu ngoài phạm vi trả `()`.

| # | Câu | Kết quả `output/parse-results.txt` | Kỳ vọng |
|---|---|---|---|
| 1 | Môn NLP có bao nhiêu tín chỉ? | `(S (Q_COURSE_INFO môn (COURSE_NAME nlp) có (HOW_MANY bao_nhiêu) (COURSE_METRIC tín_chỉ)))` | ✅ |
| 2 | CO3085 có mấy tín chỉ? | `(S (Q_COURSE_INFO (COURSE_NAME co3085) có (HOW_MANY mấy) (COURSE_METRIC tín_chỉ)))` | ✅ |
| 3 | Môn học gồm những phần nào? | `(S (Q_COURSE_INFO môn_học gồm những phần nào))` | ✅ |
| 4 | Tuần 3 học gì? | `(S (Q_SCHEDULE tuần (WEEK_NUM (CH_NUM 3)) học gì))` | ✅ |
| 5 | Chương 4 học vào tuần nào? | `(S (Q_SCHEDULE chương (CH_NUM 4) học vào tuần nào))` | ✅ |
| 6 | Chương nào nói về CFG? | `(S (Q_TOPIC chương nào (TOPIC_VERB nói) về (TOPIC_ENTITY (TOPIC_ABBR cfg))))` | ✅ |
| 7 | PCFG được học ở đâu? | `(S (Q_TOPIC (TOPIC_ENTITY (TOPIC_ABBR pcfg)) được học ở đâu))` | ✅ |
| 8 | Chương nào nói về semantic grammar? | `(S (Q_TOPIC chương nào (TOPIC_VERB nói) về (TOPIC_ENTITY (TOPIC_EN semantic_grammar))))` | ✅ |
| 9 | L.O.2.5 là gì? | `(S (Q_LO (LO_CODE lo2.5) là gì))` | ✅ (cần sửa lỗi 2) |
| 10 | L.O.4.2 liên quan đến nội dung nào? | `(S (Q_LO (LO_CODE lo4.2) liên_quan đến nội_dung nào))` | ✅ (cần sửa lỗi 2) |
| 11 | Bài tập lớn yêu cầu xây dựng những gì? | `(S (Q_ASSIGNMENT bài_tập_lớn yêu_cầu xây_dựng những gì))` | ✅ |
| 12 | Phần I của bài tập lớn là gì? | `(S (Q_ASSIGNMENT phần (PART_NUM i) của bài_tập_lớn là gì))` | ✅ |
| 13 | Bài tập lớn có phần hỏi đáp không? | `(S (Q_ASSIGNMENT bài_tập_lớn có phần (ASSIGN_PART hỏi_đáp) không))` | ✅ |
| 14 | Có được dùng LLM/RAG không? | `(S (Q_RULE có được dùng (RULE_TERM llm_rag) không))` | ✅ |
| 15 | Quy định về sử dụng AI là gì? | `(S (Q_RULE quy_định về sử_dụng (AI_TERM ai) là gì))` | ✅ |
| 16 | Midterm bao nhiêu phút? | `(S (Q_COURSE_INFO (EXAM midterm) (HOW_MANY bao_nhiêu) phút))` | ✅ |
| 17 | Final bao nhiêu phút? | `(S (Q_COURSE_INFO (EXAM final) (HOW_MANY bao_nhiêu) phút))` | ✅ |
| 18 | Tài liệu tham khảo về statistical NLP là gì? | `(S (Q_RESOURCE tài_liệu tham_khảo về (RES_TOPIC statistical_nlp) là gì))` | ✅ |
| 19 | Tài liệu nào liên quan đến Python NLP? | `(S (Q_RESOURCE tài_liệu nào liên_quan đến (RES_TOPIC python_nlp)))` | ✅ |
| 20 | Chương 12 nói về gì? | `(S (Q_TOPIC chương (CH_NUM 12) nói về gì))` | ✅ |
| 21 | Chương nào học về reference? | `(S (Q_TOPIC chương nào (TOPIC_VERB học) về (TOPIC_ENTITY (TOPIC_EN reference))))` | ✅ |
| 22 | Chương nào học về question answering? | `(S (Q_TOPIC chương nào (TOPIC_VERB học) về (TOPIC_ENTITY (TOPIC_EN question_answering))))` | ✅ |
| 23 | Chương nào học về selectional restriction? | `(S (Q_TOPIC chương nào (TOPIC_VERB học) về (TOPIC_ENTITY (TOPIC_EN selectional_restriction))))` | ✅ |
| 24 | Chương 10 có những phương pháp gì? | `(S (Q_TOPIC chương (CH_NUM 10) có những phương_pháp gì))` | ✅ |
| 25 | Chương 11 có liên quan đến hỏi đáp không? | `(S (Q_TOPIC chương (CH_NUM 11) có liên_quan đến (TOPIC_ENTITY (TOPIC_VI hỏi_đáp)) không))` | ✅ |
| 26 | Hôm nay ở TP.HCM có mưa không? | `()` | ✅ ngoài phạm vi (OOV) |
| 27 | Ai là tổng thống của Pháp? | `()` | ✅ ngoài phạm vi (`ai` có trong văn phạm nhưng `tổng`, `thống`… thì không) |
| 28 | Hãy giải bài tập xác suất này giúp tôi. | `()` | ✅ ngoài phạm vi (OOV) |
| 29 | Chương 4 nói về gì? | `(S (Q_TOPIC chương (CH_NUM 4) nói về gì))` | ✅ |
| 30 | Nó có liên quan đến parsing không? | `(S (Q_CONTEXT (CTX_REF nó) có liên_quan đến (TOPIC_ENTITY (TOPIC_EN parsing)) không))` | ✅ (cần sửa lỗi 2) |
| 31 | Chương 11 có hỏi đáp không? | `(S (Q_TOPIC chương (CH_NUM 11) có (TOPIC_ENTITY (TOPIC_VI hỏi_đáp)) không))` | ✅ |
| 32 | Còn chương sau? | `(S (Q_CONTEXT còn chương (CTX_DIR sau)))` | ✅ (cần sửa lỗi 2) |
| 33 | Bài tập lớn có phần parser không? | `(S (Q_ASSIGNMENT bài_tập_lớn có phần (ASSIGN_PART parser) không))` | ✅ |
| 34 | Phần này cần xuất file gì? | `(S (Q_CONTEXT (CTX_REF phần này) cần xuất file gì))` | ✅ (cần sửa lỗi 2) |

### 4.2. Test biên bổ sung: **16/16 PASSED**

| Câu | Kết quả | Kiểm tra điều gì |
|---|---|---|
| `""` (dòng trống) | `()` | Câu rỗng |
| `"   "` | `()` | Câu chỉ có khoảng trắng |
| Bài tập lớn nộp khi nào? | `(S (Q_DEADLINE bài_tập_lớn nộp khi nào))` | Nhóm `Q_DEADLINE` |
| Hạn nộp bài tập lớn là khi nào? | `(S (Q_DEADLINE hạn_nộp bài_tập_lớn là khi nào))` | Nhiều từ ghép liên tiếp |
| Deadline của bài tập lớn là khi nào? | `(S (Q_DEADLINE deadline của bài_tập_lớn là khi nào))` | Nhóm `Q_DEADLINE` |
| Chương 13 nói về gì? | `()` | `CH_NUM` chỉ có 1–12 |
| Tuần 15 học gì? | `(S (Q_SCHEDULE tuần (WEEK_NUM 15) học gì))` | `WEEK_NUM` có 13–15 |
| Chương nào nói về word sense disambiguation? | `(... (TOPIC_EN word_sense_disambiguation) ...)` | Lỗi 3 đã được sửa |
| Có được dùng LLM RAG không? | `(S (Q_RULE có được dùng (RULE_TERM llm_rag) không))` | Gộp từ ghép, chỉ ra 1 cây duy nhất |
| gì học 3 tuần | `()` | Đủ từ vựng nhưng sai trật tự |
| tuần 3 học gì gì | `()` | Thừa token |
| Chương 4 có CFG không? | `(S (Q_TOPIC chương (CH_NUM 4) có (TOPIC_ENTITY (TOPIC_ABBR cfg)) không))` | Nhóm `Q_TOPIC` |
| Tuần 3 học gì? (Unicode dạng **NFD**) | `(S (Q_SCHEDULE tuần (WEEK_NUM (CH_NUM 3)) học gì))` | Chuẩn hoá Unicode |
| LO 2.5 là gì? | `(S (Q_LO (LO_CODE lo2.5) là gì))` | Biến thể cách viết mã LO |
| Chuẩn đầu ra L.O.1.1 là gì? | `(S (Q_LO chuẩn_đầu_ra (LO_CODE lo1.1) là gì))` | Từ ghép kết hợp mã LO |
| Tài liệu nào liên quan đến CFG? | `(... (RES_TOPIC (TOPIC_ENTITY (TOPIC_ABBR cfg))))` | `RES_TOPIC` lồng `TOPIC_ENTITY` |

### 4.3. Tích hợp

- `python3 -m src.parser`: tạo `output/parse-results.txt` gồm 34 dòng, đúng bằng số câu input.
- `python3 -m src.main_part1`: chạy hết Phần I không lỗi, `output/grammar.txt` khớp với `models/grammar.cfg`.

---

## 5. Hạn chế

- Parser chỉ nhận đúng cách diễn đạt có trong văn phạm. Muốn nhận thêm câu hỏi hoặc từ đồng nghĩa mới thì phải bổ sung luật trong `grammar.cfg`; phần code parser không cần sửa.
- Câu nhập nhằng chỉ xuất cây đầu tiên mà ChartParser tìm được.
- Chưa xử lý lỗi chính tả hoặc câu viết không dấu (ví dụ `tuan 3 hoc gi` sẽ ra `()`).
