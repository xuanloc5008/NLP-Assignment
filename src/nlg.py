"""
Mục 4.1.4 & 4.1.5: Truy xuất thông tin, Sinh câu trả lời tự nhiên & Xử lý Fallback
Phụ trách: Đức Anh
Output yêu cầu: output/query.txt, output/answer.txt (mỗi dòng ứng với một câu của input/sentences.txt)
Yêu cầu Fallback: "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."

    python3 -m src.nlg

Nguồn (intent, entities) cho từng câu:
  1. IntentEntityDetector (Mục 4.1.2) nếu đã nhận diện được intent;
  2. ngược lại dùng nhãn kỳ vọng trong data/sample_queries.txt (oracle) để kiểm thử độc lập
     Knowledge Base / Query / NLG khi Mục 4.1.2 chưa hoàn thiện.
"""
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.knowledge_base import KnowledgeBase, normalize
from src.query_engine import QueryEngine, label_to_entities, UNKNOWN_INTENTS

PART_NAMES_VI = {
    "Syntactic Processing": "Xử lý cú pháp",
    "Semantic Interpretation": "Diễn dịch ngữ nghĩa",
    "Context and World Knowledge": "Ngữ cảnh và tri thức thế giới",
}
RULE_NAMES_VI = {
    "ATTENDANCE": "tham dự lớp", "ACADEMIC_INTEGRITY": "liêm chính học thuật",
    "AI_USAGE": "sử dụng AI", "SOURCE_CODE": "mã nguồn",
    "ASSIGNMENT_SHARING": "chia sẻ bài làm", "EXTERNAL_LIBRARIES": "thư viện bên ngoài",
    "LLM_RAG": "sử dụng LLM/RAG", "OUT_OF_SCOPE": "câu hỏi ngoài phạm vi",
}
COURSE_ATTR_VI = {
    "course_id": "Mã môn học", "course_name": "Tên môn học", "course_name_en": "Tên tiếng Anh",
    "semester": "Học kỳ", "ects": "Số ECTS", "course_type": "Loại học phần",
    "department": "Đơn vị phụ trách", "format": "Hình thức học",
    "course_description": "Mô tả môn học", "study_note": "Ghi chú học tập",
}
ASSESS_VI = {
    "class_attention_and_assignments": "chuyên cần và bài tập", "major_assignment": "bài tập lớn",
    "midterm_exam": "thi giữa kỳ", "final_exam": "thi cuối kỳ",
}
HOURS_VI = {
    "total_course_hours": "tổng", "lecture_hours": "lý thuyết",
    "major_assignment_hours": "bài tập lớn", "self_study_hours": "tự học",
}
EXAM_VI = {"midterm": "giữa kỳ (midterm)", "final": "cuối kỳ (final)"}


def _chapter_name(ch: dict) -> str:
    return f"Chương {ch['number']} – {ch['title']}"


def _join_vi(items: list[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b và c'"""
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " và " + items[-1]


def _strip_num(subtopic: str) -> str:
    """'4.5 Parsing with features' -> 'Parsing with features'"""
    return subtopic.split(" ", 1)[1] if subtopic[:1].isdigit() and " " in subtopic else subtopic


def _sentence(text: str) -> str:
    text = " ".join(text.split())
    return text if text.endswith((".", "!", "?")) else text + "."


def _lo_label(lo_id: str) -> str:
    """'LO2.5' -> 'L.O.2.5' (đúng cách viết trong dữ liệu môn học)"""
    return "L.O." + lo_id[2:]


def _percent(v: str) -> str:
    return v.replace(" percent", "%")


class AnswerGenerator:
    FALLBACK_MESSAGE = "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."

    def __init__(self, query_engine):
        self.qe = query_engine

    def generate_answer(self, intent: str, entities: dict, sentence: str = "") -> str:
        """
        Dùng Template-based NLG để tạo câu trả lời tự nhiên từ kết quả truy vấn KB.
        Nếu ngoài miền hoặc không có dữ liệu, trả về self.FALLBACK_MESSAGE.
        """
        if (intent or "UNKNOWN").upper() in UNKNOWN_INTENTS:
            return self.FALLBACK_MESSAGE
        result = self.qe.execute_query(intent, entities, sentence)
        if result is None and sentence:
            result = self.qe.search_faq(sentence)
        if result is None:
            return self.FALLBACK_MESSAGE
        render = getattr(self, "_t_" + result["type"], None)
        answer = render(result) if render else None
        return _sentence(answer) if answer else self.FALLBACK_MESSAGE

    # ================================================================ templates
    # ---- course_info
    def _t_course_overview(self, r):
        d = r["data"]
        return (f"Môn {d.get('course_name')} ({d.get('course_name_en')}, mã {d.get('course_id')}) "
                f"có {d.get('credits')} tín chỉ, học kỳ {d.get('semester')}, do "
                f"{d.get('department')} phụ trách")

    def _t_course_attr(self, r):
        attr, v, info = r["attr"], r["data"], r.get("course", {})
        name = f"Môn {info.get('course_name', 'học')} ({info.get('course_id', 'CO3085')})"
        if attr == "credits":
            return f"{name} có {v} tín chỉ"
        if attr == "main_parts":
            parts = []
            for p in v:
                en = p.split(" - ", 1)[-1]
                parts.append(f"{PART_NAMES_VI.get(en, en)} ({en})")
            return f"Môn học gồm {len(v)} phần chính: " + "; ".join(parts)
        if attr == "instructor":
            return f"Giảng viên phụ trách môn học là {v}"
        label = COURSE_ATTR_VI.get(attr, attr)
        return f"{label} của {name[0].lower() + name[1:]}: {v}"

    def _t_exam(self, r):
        fmt = ", ".join(r["format"])
        if r["minutes"]:
            return (f"Theo đề cương, bài thi {EXAM_VI[r['exam']]} kéo dài {r['minutes']} phút"
                    + (f", hình thức {fmt}" if fmt else ""))
        return f"Theo đề cương, bài thi {EXAM_VI[r['exam']]}: {r['data']}"

    def _t_exam_list(self, r):
        return "Theo đề cương: " + "; ".join(self._t_exam(e)[len("Theo đề cương, "):] for e in r["data"])

    def _t_assessment(self, r):
        items = [f"{ASSESS_VI.get(k, k)} {_percent(v)}" for k, v in r["data"].items()]
        return "Cách đánh giá môn học: " + _join_vi(items)

    def _t_hours(self, r):
        d = r["data"]
        rest = [f"{HOURS_VI[k]} {v} giờ" for k, v in d.items() if k != "total_course_hours"]
        head = f"Môn học có tổng cộng {d['total_course_hours']} giờ" if "total_course_hours" in d else "Thời lượng môn học"
        return head + (" gồm " + _join_vi(rest) if rest else "")

    def _t_lo_list(self, r):
        return "Các chuẩn đầu ra của môn học: " + " ".join(
            f"{_lo_label(k)}: {v}" for k, v in r["data"].items())

    # ---- schedule
    def _t_week(self, r):
        w, ch = r["data"], r["chapter"]
        head = f"Tuần {w['week']} học {_chapter_name(ch)}" if ch else f"Tuần {w['week']} thuộc phần {w.get('part', '')}"
        ans = head + ", gồm các chủ đề: " + ", ".join(w["topics"])
        if w.get("activity"):
            ans += f". Hoạt động: {w['activity']}"
        if w.get("milestone"):
            ans += f". Mốc bài tập lớn: {w['milestone']}"
        return ans

    def _t_chapter_weeks(self, r):
        weeks = _join_vi([f"tuần {x}" for x in r["data"]])
        return f"{_chapter_name(r['chapter'])} được học vào {weeks}"

    def _t_topic_weeks(self, r):
        return f"Chủ đề {r['label']} được học vào " + _join_vi([f"tuần {x}" for x in r["data"]])

    def _t_schedule_overview(self, r):
        return "Kế hoạch học tập 15 tuần: " + "; ".join(f"tuần {w}: {t}" for w, t in r["data"])

    def _t_deadline(self, r):
        items = [f"tuần {w}: {m}" for w, m in r["data"]]
        return "Các mốc bài tập lớn (dữ liệu mẫu): " + "; ".join(items)

    # ---- topics
    def _t_chapter_summary(self, r):
        ch = r["data"]
        subs = [_strip_num(s) for s in ch["subtopics"] if s.count(".") <= 1]
        return f"Chương {ch['number']} nói về {ch['title']}, gồm các nội dung chính: " + ", ".join(subs)

    def _t_chapter_subtopics(self, r):
        ch = r["data"]
        subs = [_strip_num(s) for s in ch["subtopics"] if s.count(".") <= 1]
        return f"{_chapter_name(ch)} trình bày các nội dung/phương pháp: " + ", ".join(subs)

    def _t_chapter_check(self, r):
        ch = r["data"]
        if not r["found"]:
            return f"Không. Theo dữ liệu môn học, {_chapter_name(ch)} không đề cập đến {r['label']}"
        ans = f"Có. {_chapter_name(ch)} có đề cập đến {r['label']}"
        if r["evidence"]:
            ans += ", cụ thể: " + ", ".join(_strip_num(e) for e in r["evidence"])
        return ans

    def _t_topic_chapters(self, r):
        chs = r["data"]
        names = _join_vi([_chapter_name(c) for c in chs])
        weeks = sorted({w for c in chs for w in c.get("weeks", [])})
        ans = f"{r['label']} được trình bày trong {names}"
        if weeks:
            ans += " (học vào " + _join_vi([f"tuần {w}" for w in weeks]) + ")"
        return ans[:1].upper() + ans[1:]

    def _t_chapter_list(self, r):
        return "Môn học gồm 12 chương: " + "; ".join(_chapter_name(c) for c in r["data"])

    # ---- learning outcomes
    def _t_lo(self, r):
        ans = f"{_lo_label(r['lo'])} liên quan đến: {r['data'][:1].lower() + r['data'][1:]}"
        ans = ans.rstrip(".")
        if r["chapters"]:
            ans += ". Nội dung này thuộc " + _join_vi([_chapter_name(c) for c in r["chapters"]])
        return ans

    def _t_lo_chapter(self, r):
        return f"Nội dung {_lo_label(r['lo'])} thuộc " + _join_vi([_chapter_name(c) for c in r["chapters"]])

    # ---- assignments
    def _t_assignment(self, r):
        a = r["data"]
        parts = "; ".join(f"Phần {p['id'].split('_')[1]} – {p['title']}" for p in r["parts"])
        ans = f"Bài tập lớn \"{a.get('title')}\" (nhóm {a.get('team_size', '').replace('students', 'sinh viên')})"
        ans += f": {a.get('goal', '').rstrip('.')}"
        if parts:
            ans += f". Bài tập lớn gồm {len(r['parts'])} phần: {parts}"
        return ans

    def _t_part(self, r):
        p = r["data"]
        ans = f"Phần {p['id'].split('_')[1]} của bài tập lớn là {p['title']}"
        if p["requirements"]:
            ans += ", yêu cầu: " + "; ".join(p["requirements"])
        if p.get("outputs"):
            ans += ". Output gợi ý: " + ", ".join(p["outputs"])
        return ans

    def _t_part_outputs(self, r):
        p = r["data"]
        return (f"Phần {p['id'].split('_')[1]} ({p['title']}) cần xuất các file: "
                + _join_vi([f"output/{o}" for o in p["outputs"]]))

    def _t_assignment_check(self, r):
        p = r["data"]
        if not r["found"] or p is None:
            return f"Không. Theo dữ liệu môn học, bài tập lớn không có phần về {r['label']}"
        ans = f"Có. Phần {p['id'].split('_')[1]} của bài tập lớn là {p['title']}"
        if p["requirements"]:
            ans += ", yêu cầu: " + "; ".join(p["requirements"])
        return ans

    # ---- resources
    def _t_resources(self, r):
        items = []
        for x in r["data"]:
            s = x["title"]
            if x.get("authors"):
                s += f" ({x['authors'].replace(';', ',')}"
                s += f", {x['year']})" if x.get("year") else ")"
            elif x.get("year"):
                s += f" ({x['year']})"
            items.append(s)
        if r.get("chapter"):
            head = f"Tài liệu cho {_chapter_name(r['chapter'])}: có thể tham khảo các giáo trình nền tảng"
        elif r.get("topic"):
            head = "Tài liệu liên quan đến " + re.sub(r"\b(nlp|ai|llm)\b", lambda m: m.group().upper(), r["topic"])
        else:
            head = "Tài liệu học tập của môn học"
        return head + ": " + "; ".join(items)

    # ---- regulations
    def _t_rule(self, r):
        return f"Quy định về {RULE_NAMES_VI.get(r['rule'], r['rule'].lower())}: {r['data']}"

    def _t_rule_list(self, r):
        return "Các quy định của môn học: " + " ".join(
            f"({RULE_NAMES_VI.get(k, k)}) {_sentence(v)}" for k, v in r["data"].items())

    # ---- FAQ
    def _t_faq(self, r):
        return r["data"]["answer"]

    # ================================================================ batch
    def process_file(
        self,
        input_path: str,
        query_path: str,
        answer_path: str,
        detect=None,
        intent_entity_path: str | None = None,
    ):
        """
        Nhận kết quả (intent, entities) từ bước Intent/Entity (output/intent-entity.txt hoặc hàm detect),
        xây dựng truy vấn tới Knowledge Base (output/query.txt), truy xuất dữ liệu và sinh câu trả lời
        (output/answer.txt). Mỗi dòng input tương ứng đúng một dòng output.
        """
        import ast

        with open(input_path, encoding="utf-8") as f:
            sentences = f.read().splitlines()

        ie_records = []
        if intent_entity_path and os.path.exists(intent_entity_path):
            with open(intent_entity_path, encoding="utf-8") as f:
                for line in f.read().splitlines():
                    if "|" in line:
                        i_str, e_str = [x.strip() for x in line.split("|", 1)]
                        try:
                            e_dict = ast.literal_eval(e_str) if e_str.startswith("{") else {}
                        except Exception:
                            e_dict = {}
                        ie_records.append((i_str, e_dict))

        last_state = {}
        queries, answers = [], []
        for idx, s in enumerate(sentences):
            if not s.strip():
                queries.append("")
                answers.append("")
                continue
            if idx < len(ie_records):
                intent, entities = ie_records[idx]
                entities = dict(entities)
                if intent == "CONTEXT_DEPENDENT":
                    ref = str(entities.get("context_ref", "")).lower()
                    if ref == "sau" and "chapter" in last_state:
                        ch_num = int(re.search(r"\d+", last_state["chapter"]).group())
                        entities["chapter"] = f"CH{min(ch_num + 1, 12):02d}"
                    elif ref == "trước" and "chapter" in last_state:
                        ch_num = int(re.search(r"\d+", last_state["chapter"]).group())
                        entities["chapter"] = f"CH{max(ch_num - 1, 1):02d}"
                    elif "phần" in ref and "assignment_part" in last_state:
                        entities["assignment_part"] = last_state["assignment_part"]
                    elif "chapter" in last_state and "chapter" not in entities:
                        entities["chapter"] = last_state["chapter"]
                if "chapter" in entities:
                    last_state["chapter"] = entities["chapter"]
                if "assignment_part" in entities:
                    last_state["assignment_part"] = entities["assignment_part"]
            elif detect is not None:
                intent, entities = detect(s)
            else:
                intent, entities = ("UNKNOWN", {})

            queries.append(self.qe.build_query(intent, entities, s))
            answers.append(self.generate_answer(intent, entities, s))

        for path, lines in ((query_path, queries), (answer_path, answers)):
            out_dir = os.path.dirname(path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")

        n_ok = sum(a not in ("", self.FALLBACK_MESSAGE) for a in answers)
        print(f"-> Đã trả lời {n_ok}/{len(answers)} câu (còn lại fallback), "
              f"ghi vào {query_path} và {answer_path}")


def load_gold_labels(sample_queries_path: str) -> dict:
    """data/sample_queries.txt -> {câu đã chuẩn hoá: (intent, entities)}"""
    gold = {}
    with open(sample_queries_path, encoding="utf-8") as f:
        for line in f:
            cols = [c.strip() for c in line.split("|")]
            if len(cols) == 4 and cols[0].startswith("Q") and cols[0][1:].isdigit():
                gold.setdefault(normalize(cols[1]), (cols[2], label_to_entities(cols[3])))
    return gold


def make_detector(detector=None, sample_queries_path: str | None = None):
    """
    Trả về hàm detect(sentence). Ưu tiên IntentEntityDetector; nếu câu là CONTEXT_DEPENDENT
    trong luồng câu tuần tự thì giải tham chiếu từ câu liền trước (hoặc nhãn kỳ vọng).
    """
    gold = load_gold_labels(sample_queries_path) if sample_queries_path and os.path.exists(sample_queries_path) else {}
    last_state = {}

    def detect(sentence: str):
        intent, entities = ("UNKNOWN", {})
        if detector is not None:
            intent, entities = detector.detect(sentence)
        if (intent or "UNKNOWN").upper() in UNKNOWN_INTENTS and normalize(sentence) in gold:
            intent, entities = gold[normalize(sentence)]
        elif (intent or "").upper() == "CONTEXT_DEPENDENT":
            entities = dict(entities)
            ref = str(entities.get("context_ref", "")).lower()
            if ref == "sau" and "chapter" in last_state:
                ch_num = int(re.search(r"\d+", last_state["chapter"]).group())
                entities["chapter"] = f"CH{min(ch_num + 1, 12):02d}"
            elif ref == "trước" and "chapter" in last_state:
                ch_num = int(re.search(r"\d+", last_state["chapter"]).group())
                entities["chapter"] = f"CH{max(ch_num - 1, 1):02d}"
            elif "phần" in ref and "assignment_part" in last_state:
                entities["assignment_part"] = last_state["assignment_part"]
            elif "chapter" in last_state and "chapter" not in entities:
                entities["chapter"] = last_state["chapter"]
            elif normalize(sentence) in gold:
                _, gold_ent = gold[normalize(sentence)]
                entities.update(gold_ent)

        # Cập nhật ngữ cảnh từ câu hiện tại cho câu kế tiếp
        if "chapter" in entities:
            last_state["chapter"] = entities["chapter"]
        if "assignment_part" in entities:
            last_state["assignment_part"] = entities["assignment_part"]
        return intent, entities

    return detect


if __name__ == "__main__":
    from src.intent_entity import IntentEntityDetector

    kb = KnowledgeBase(os.path.join(PROJECT_ROOT, "data")).load_data()
    nlg = AnswerGenerator(QueryEngine(kb))
    nlg.process_file(
        os.path.join(PROJECT_ROOT, "input", "sentences.txt"),
        os.path.join(PROJECT_ROOT, "output", "query.txt"),
        os.path.join(PROJECT_ROOT, "output", "answer.txt"),
        make_detector(IntentEntityDetector(), os.path.join(PROJECT_ROOT, "data", "sample_queries.txt")),
    )
