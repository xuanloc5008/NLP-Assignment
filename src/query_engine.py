"""
Mục 4.1.3 + 4.1.4: Xây dựng truy vấn tới Knowledge Base và truy xuất thông tin
Phụ trách: Đức Anh
Output yêu cầu: output/query.txt

Luồng xử lý:
    (intent, entities, câu gốc) --normalize--> slot chuẩn hoá
                                 --plan------> {table, select, where}
                                 --build-----> "SELECT credits FROM course_info WHERE course_id='CO3085'"
                                 --execute---> dict kết quả (đưa cho NLG) hoặc None (không tìm thấy)

Schema entity (dict) mà module chấp nhận - giá trị có thể ở dạng mã chuẩn hoặc dạng tự nhiên:
    course          : 'CO3085' | 'NLP' | 'Natural Language Processing'
    week            : 'WEEK_03' | 'Tuần 3' | 3
    chapter         : 'CH04' | 'Chương 4' | 4
    topic           : 'CFG' | 'SEMANTIC_GRAMMAR' | 'semantic grammar' | 'hỏi đáp'
    lo              : 'LO2.5' | 'L.O.2.5'
    assignment      : 'BTL01'
    assignment_part : 'PART_I' | 'Phần I' | 'Part I'
    rule_topic      : 'AI_USAGE' | 'LLM_RAG' | 'LLM/RAG'
    exam            : 'MIDTERM' | 'FINAL'
    resource_topic  : 'STATISTICAL_NLP' | 'Python NLP'
    attribute       : (tuỳ chọn) thuộc tính cần hỏi, ví dụ 'credits', 'outputs', 'weeks'
Nhãn phẳng như trong sample_queries.txt ('CH04', 'WEEK_03', 'LO2.5'...) đổi sang dict bằng label_to_entities().
"""
import re

from src.knowledge_base import LO_CHAPTERS, normalize

UNKNOWN_INTENTS = {"UNKNOWN", "OUT_OF_SCOPE", "", None}
NO_QUERY = "NO_QUERY"

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}
_ROMAN_REV = {v: k for k, v in _ROMAN.items()}

# Từ khoá bổ sung ngoài entities.txt (để so khớp câu hỏi với nội dung tiếng Anh trong data/)
TOPIC_EXTRA_TERMS = {
    "QUESTION_ANSWERING": ["qa"],
    "FEATURES": ["feature", "feature systems"],
    "PARSING": ["parsing", "parser", "phân tích cú pháp"],
    "AMBIGUITY": ["ambiguity", "nhập nhằng"],
    "SEMANTICS": ["semantics", "ngữ nghĩa"],
    "PROBABILITY": ["probability", "xác suất"],
    "DISCOURSE": ["discourse"],
    "ELLIPSIS": ["ellipsis", "tỉnh lược"],
    "FRAMES": ["frames", "frame"],
    "SYNTAX": ["syntax", "cú pháp"],
    "MACHINE_TRANSLATION": ["machine translation", "dịch máy"],
}

# Từ khoá trong câu -> mã quy định trong regulations.txt
RULE_KEYWORDS = [
    ("LLM_RAG", ["llm", "rag"]),
    ("AI_USAGE", ["ai", "trí tuệ nhân tạo", "chatgpt"]),
    ("ASSIGNMENT_SHARING", ["sao chép", "chia sẻ", "copy"]),
    ("EXTERNAL_LIBRARIES", ["thư viện", "library"]),
    ("ACADEMIC_INTEGRITY", ["liêm chính", "gian lận", "đạo văn"]),
    ("SOURCE_CODE", ["mã nguồn", "source code"]),
    ("ATTENDANCE", ["điểm danh", "tham dự", "đi học", "vắng"]),
    ("OUT_OF_SCOPE", ["ngoài phạm vi"]),
]

# Từ khoá trong câu -> thuộc tính của course_info (xét theo thứ tự)
COURSE_ATTR_KEYWORDS = [
    ("credits", ["tín chỉ", "credit"]),
    ("ects", ["ects"]),
    ("midterm", ["midterm", "giữa kỳ", "giữa kì"]),
    ("final", ["final", "cuối kỳ", "cuối kì"]),
    ("exam_format", ["thi", "kiểm tra"]),
    ("assessment", ["đánh giá", "điểm", "tỉ lệ", "tỷ lệ", "trọng số"]),
    ("hours", ["giờ", "thời lượng", "tiết"]),
    ("main_parts", ["phần", "part"]),
    ("learning_outcomes", ["chuẩn đầu ra", "learning outcome"]),
    ("department", ["khoa", "bộ môn"]),
    ("semester", ["học kỳ", "học kì", "semester"]),
    ("instructor", ["giảng viên", "giáo viên", "phụ trách"]),
    ("course_name", ["tên"]),
    ("course_description", ["mô tả", "mục tiêu", "giới thiệu", "nội dung"]),
]

_YESNO_RE = re.compile(r"\bkhông\s*[?.!]*\s*$")


def _contains(text: str, term: str) -> bool:
    """So khớp nguyên cụm từ (không khớp 'cfg' bên trong 'pcfg')."""
    return re.search(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", text) is not None


def _roman(n: int) -> str:
    return _ROMAN_REV.get(n, str(n))


def label_to_entities(label: str) -> dict:
    """
    Đổi nhãn phẳng (EXPECTED_ENTITY của sample_queries.txt) sang dict slot:
        'CH04' -> {'chapter': 'CH04'}, 'WEEK_03' -> {'week': 'WEEK_03'}, 'PART_I' -> {'assignment_part': 'PART_I'}
    """
    label = (label or "").strip()
    up = label.upper()
    if not label or up == "OUT_OF_SCOPE":
        return {}
    if re.fullmatch(r"CH\d+", up):
        return {"chapter": up}
    if re.fullmatch(r"WEEK_\d+", up):
        return {"week": up}
    if re.fullmatch(r"LO\d+(\.\d+)?", up):
        return {"lo": up}
    if re.fullmatch(r"PART_[IV]+", up):
        return {"assignment_part": up}
    if re.fullmatch(r"BTL\d+", up):
        return {"assignment": up}
    if up in ("CO3085", "NLP"):
        return {"course": "CO3085"}
    if up in ("MIDTERM", "FINAL"):
        return {"exam": up}
    if up in ("AI_USAGE", "LLM_RAG", "ATTENDANCE", "ACADEMIC_INTEGRITY", "SOURCE_CODE",
              "ASSIGNMENT_SHARING", "EXTERNAL_LIBRARIES"):
        return {"rule_topic": up}
    if up.endswith("_NLP"):
        return {"resource_topic": up}
    return {"topic": up}


class QueryEngine:
    def __init__(self, kb):
        self.kb = kb
        # Lexicon chủ đề: entities.txt + từ khoá bổ sung
        self.topic_terms = {k: list(v) for k, v in kb.lexicon.items()}
        for key, extra in TOPIC_EXTRA_TERMS.items():
            terms = self.topic_terms.setdefault(key, [])
            terms += [t for t in extra if t not in terms]

    # ================================================================ chuẩn hoá
    def normalize_entities(self, intent: str, entities: dict, sentence: str = "") -> dict:
        """Đưa giá trị entity về mã chuẩn và bổ sung slot suy ra được từ câu gốc."""
        ent = {}
        for k, v in (entities or {}).items():
            if v is None or v == "":
                continue
            if isinstance(v, (list, tuple)):
                v = v[0] if v else None
                if v is None:
                    continue
            ent[k.lower()] = v

        if "lo_code" in ent and "lo" not in ent:
            ent["lo"] = ent.pop("lo_code")
        if "rule_term" in ent and "rule_topic" not in ent:
            ent["rule_topic"] = ent.pop("rule_term")
        if "assignment_id" in ent and "assignment" not in ent:
            ent["assignment"] = ent.pop("assignment_id")

        if "chapter" in ent:
            ent["chapter"] = self._norm_chapter(ent["chapter"])
        if "week" in ent:
            ent["week"] = self._norm_week(ent["week"])
        if "lo" in ent:
            ent["lo"] = self._norm_lo(ent["lo"])
        if "assignment_part" in ent:
            ent["assignment_part"] = self._norm_part(ent["assignment_part"])
        if "rule_topic" in ent:
            ent["rule_topic"] = re.sub(r"\W+", "_", str(ent["rule_topic"]).upper()).strip("_")
        if "exam" in ent:
            ent["exam"] = str(ent["exam"]).upper()
        if "course" in ent:
            ent["course"] = "CO3085"
        if "topic" in ent:
            ent["topic"] = self._norm_topic(ent["topic"])
            if ent["topic"] is None:
                ent.pop("topic")

        s = normalize(sentence)
        if s:
            # Slot có thể đọc trực tiếp từ câu khi bộ nhận diện chưa trích được
            if "chapter" not in ent:
                m = re.search(r"chương\s+(\d+)", s)
                if m:
                    ent["chapter"] = f"CH{int(m.group(1)):02d}"
            if "week" not in ent:
                m = re.search(r"tuần\s+(\d+)", s)
                if m:
                    ent["week"] = f"WEEK_{int(m.group(1)):02d}"
            if "lo" not in ent:
                m = re.search(r"\bl\.?\s*o\.?\s*(\d+(?:\.\d+)?)", s)
                if m:
                    ent["lo"] = "LO" + m.group(1)
            if "topic" not in ent:
                topic = self.find_topic_in_text(s)
                if topic:
                    ent["topic"] = topic
        return ent

    @staticmethod
    def _norm_chapter(v) -> str:
        m = re.search(r"\d+", str(v))
        return f"CH{int(m.group()):02d}" if m else str(v).upper()

    @staticmethod
    def _norm_week(v) -> str:
        m = re.search(r"\d+", str(v))
        return f"WEEK_{int(m.group()):02d}" if m else str(v).upper()

    @staticmethod
    def _norm_lo(v) -> str:
        m = re.search(r"(\d+(?:\.\d+)?)", str(v))
        return "LO" + m.group(1) if m else str(v).upper()

    @staticmethod
    def _norm_part(v) -> str:
        v = str(v).upper()
        m = re.search(r"\b([IV]+)\s*$", v.replace("_", " "))
        if m:
            return f"PART_{m.group(1)}"
        m = re.search(r"\d+", v)
        return f"PART_{_roman(int(m.group()))}" if m else v

    def _norm_topic(self, v) -> str | None:
        key = re.sub(r"\W+", "_", str(v).upper()).strip("_")
        if key in self.topic_terms:
            return key
        return self.find_topic_in_text(normalize(str(v).replace("_", " "))) or key

    def find_topic_in_text(self, text: str) -> str | None:
        """Chủ đề có cụm từ dài nhất xuất hiện trong text."""
        best, best_len = None, 0
        for key, terms in self.topic_terms.items():
            for t in terms:
                if len(t) > best_len and _contains(text, t):
                    best, best_len = key, len(t)
        return best

    # ================================================================ lập kế hoạch
    def plan(self, intent: str, entities: dict, sentence: str = "") -> dict | None:
        """
        Xác định bảng, thuộc tính cần lấy và điều kiện lọc.
        Trả về None nếu câu ngoài miền (intent UNKNOWN).
        """
        ent = self.normalize_entities(intent, entities, sentence)
        intent = (intent or "UNKNOWN").upper()
        if intent in UNKNOWN_INTENTS:
            return None
        s = normalize(sentence)
        yesno = bool(s) and _YESNO_RE.search(s) is not None and "có" in s.split()

        if intent in ("CONTEXT_DEPENDENT", "GET_CONTEXT"):
            intent = self._intent_from_slots(ent, s)
            if intent is None:
                return None

        p = {"intent": intent, "entities": ent, "yesno": yesno, "where": {}}
        handler = getattr(self, "_plan_" + intent.lower(), None)
        if handler is None:
            return None
        return handler(p, ent, s)

    @staticmethod
    def _intent_from_slots(ent: dict, s: str) -> str | None:
        """Câu phụ thuộc ngữ cảnh đã được giải tham chiếu: suy ra intent từ loại slot."""
        if "tài liệu" in s or "giáo trình" in s:
            return "GET_RESOURCE"
        if "lo" in ent:
            return "GET_LO"
        if "assignment_part" in ent or "assignment" in ent:
            return "GET_ASSIGNMENT"
        if "tuần" in s or ("week" in ent and "chapter" not in ent):
            return "GET_SCHEDULE"
        if "chapter" in ent or "topic" in ent:
            return "GET_TOPIC"
        return None

    def _plan_get_course_info(self, p, ent, s):
        attr = ent.get("attribute")
        if not attr and ent.get("exam") in ("MIDTERM", "FINAL"):
            attr = ent["exam"].lower()
        if not attr:
            attr = next((a for a, kws in COURSE_ATTR_KEYWORDS if any(_contains(s, k) for k in kws)),
                        "overview")
        p.update(table="course_info", select=attr, where={"course_id": "CO3085"})
        return p

    def _plan_get_schedule(self, p, ent, s):
        p["table"] = "schedule"
        if "week" in ent:
            p.update(select="chapter, topics", where={"week": ent["week"]})
        elif "chapter" in ent:
            p.update(select="week", where={"chapter": ent["chapter"]})
        elif "topic" in ent:
            p.update(select="week", where={"topic": ent["topic"]})
        elif "milestone" in s or "checkpoint" in s or "mốc" in s:
            p.update(select="week, milestone", where={})
        else:
            p.update(select="week, chapter", where={})
        return p

    def _plan_get_topic(self, p, ent, s):
        p["table"] = "topics"
        if "chapter" in ent:
            p["where"] = {"chapter_id": ent["chapter"]}
            if p["yesno"] and "topic" in ent:
                p.update(select="contains", check=ent["topic"])
            elif "phương pháp" in s or "nội dung" in s or "chủ đề" in s or "những" in s:
                p["select"] = "subtopics"
            else:
                p["select"] = "title, summary"
        elif "topic" in ent:
            p.update(select="chapter_id", where={"topic": ent["topic"]})
        else:
            p.update(select="chapter_id, title", where={})
        return p

    def _plan_get_lo(self, p, ent, s):
        p["table"] = "learning_outcomes"
        if "lo" in ent:
            p["where"] = {"lo_id": ent["lo"]}
            p["select"] = "chapter" if "chương" in s else "description"
        else:
            p.update(select="lo_id, description", where={})
        return p

    def _plan_get_assignment(self, p, ent, s):
        p["table"] = "assignments"
        part = ent.get("assignment_part")
        check = ent.get("topic")
        if p["yesno"] and not part and check:
            # 'Bài tập lớn có phần parser không?' -> tìm phần có chứa chủ đề
            part = self._find_part(check)
            p["check"] = check
        elif p["yesno"] and part and check:
            p["check"] = check
        if part:
            p["where"] = {"assignment_id": "BTL01", "part": part}
            if any(k in s for k in ("file", "xuất", "output")):
                p["select"] = "outputs"
            elif "check" in p:
                p["select"] = "contains"
            else:
                p["select"] = "title, requirements"
        elif p["yesno"] and check:
            p.update(select="contains", where={"assignment_id": "BTL01", "part": None})
        else:
            p.update(select="goal, parts", where={"assignment_id": ent.get("assignment", "BTL01")})
        return p

    def _plan_get_deadline(self, p, ent, s):
        where = {}
        if "assignment_part" in ent:
            where["part"] = ent["assignment_part"]
        elif "final" in s or "cuối" in s or "nộp" in s:
            where["milestone"] = "final"
        p.update(table="schedule", select="week, milestone", where=where)
        return p

    def _plan_get_resource(self, p, ent, s):
        p["table"] = "resources"
        topic = ent.get("resource_topic")
        if not topic:
            m = re.search(r"(?:về|liên quan đến|cho)\s+(.+?)(?:\s+là gì|\s+nào|\s*\?|$)", s)
            if m and "chương" not in m.group(1):
                topic = m.group(1).strip()
        if topic:
            p.update(select="title, authors", where={"usage": normalize(str(topic).replace("_", " "))})
        elif "giáo trình" in s:
            p.update(select="title, authors", where={"type": "textbook"})
        elif "chapter" in ent:
            p.update(select="title, authors", where={"chapter": ent["chapter"], "type": "textbook"})
        else:
            p.update(select="title, authors", where={})
        return p

    def _plan_get_rule(self, p, ent, s):
        rule = ent.get("rule_topic")
        if not rule:
            rule = next((r for r, kws in RULE_KEYWORDS if any(_contains(s, k) for k in kws)), None)
        p.update(table="regulations", select="content", where={"rule": rule} if rule else {})
        return p

    def _plan_get_instructor(self, p, ent, s):
        p.update(table="course_info", select="instructor", where={"course_id": "CO3085"})
        return p

    # ================================================================ build query
    def build_query(self, intent: str, entities: dict, sentence: str = "") -> str:
        """
        Chuyển đổi (intent, entities) hoặc semantic representation thành câu truy vấn tương ứng.
        Ví dụ: "SELECT chapter, topics FROM schedule WHERE week='WEEK_03'"
        """
        p = self.plan(intent, entities, sentence)
        if p is None:
            return f"{NO_QUERY} -- intent={(intent or 'UNKNOWN').upper()} (ngoài phạm vi)"
        return self._format(p)

    @staticmethod
    def _format(p: dict) -> str:
        q = f"SELECT {p['select']} FROM {p['table']}"
        conds = []
        for k, v in p["where"].items():
            if v is None:
                continue
            op = "LIKE" if k in ("usage", "topic") else "="
            val = f"%{v}%" if op == "LIKE" else v
            conds.append(f"{k} {op} '{val}'")
        if p.get("check"):
            conds.append(f"text CONTAINS '{p['check']}'")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        return q

    # ================================================================ execute
    def execute_query(self, intent: str, entities: dict, sentence: str = "") -> dict | None:
        """
        Thực thi truy vấn trên đối tượng KnowledgeBase để lấy thông tin.
        Trả về dict {'type': ..., 'data': ...} cho NLG, hoặc None nếu không tìm thấy dữ liệu.
        """
        p = self.plan(intent, entities, sentence)
        if p is None:
            return None
        exec_fn = getattr(self, "_exec_" + p["table"], None)
        result = exec_fn(p) if exec_fn else None
        if result is None:
            return None
        result.update(intent=p["intent"], query=self._format(p), entities=p["entities"])
        return result

    # ---------------------------------------------------------------- course_info
    def _exec_course_info(self, p):
        info, attr = self.kb.course_info, p["select"]
        if not info:
            return None
        if attr == "instructor":
            return self._value("instructor", info.get("instructor"))
        if attr in ("midterm", "final"):
            return self._exam(attr)
        if attr == "exam_format":
            exams = [self._exam(a) for a in ("midterm", "final")]
            exams = [e for e in exams if e]
            return {"type": "exam_list", "data": exams} if exams else None
        if attr == "assessment":
            keys = ["class_attention_and_assignments", "major_assignment", "midterm_exam", "final_exam"]
            data = {k: info[k] for k in keys if k in info}
            return {"type": "assessment", "data": data} if data else None
        if attr == "hours":
            keys = ["total_course_hours", "lecture_hours", "major_assignment_hours", "self_study_hours"]
            data = {k: info[k] for k in keys if k in info}
            return {"type": "hours", "data": data} if data else None
        if attr == "learning_outcomes":
            data = {k: v for k, v in self.kb.los.items() if "." not in k}
            return {"type": "lo_list", "data": data} if data else None
        if attr == "overview":
            return {"type": "course_overview", "data": info}
        return self._value(attr, info.get(attr), course=info)

    @staticmethod
    def _value(attr, value, **extra):
        if not value:
            return None
        return {"type": "course_attr", "attr": attr, "data": value, **extra}

    def _exam(self, which):
        raw = self.kb.course_info.get(which)
        if not raw:
            return None
        m = re.search(r"(\d+)\s*minutes?", raw)
        fmt = [x.strip() for x in raw.split(",") if "minute" not in x]
        return {"type": "exam", "exam": which, "minutes": int(m.group(1)) if m else None,
                "format": fmt, "data": raw}

    # ---------------------------------------------------------------- schedule
    def _exec_schedule(self, p):
        w, sched = p["where"], self.kb.schedule
        if p["select"] == "week, milestone":
            ms = [(wk["week"], wk["milestone"]) for wk in sched.values() if wk.get("milestone")]
            if "part" in w:
                part = self.kb.assignments.get(w["part"], {})
                title = normalize(part.get("title", ""))
                words = [x for x in re.split(r"\W+", title) if len(x) > 3]
                ms = [m for m in ms if words and all(x in normalize(m[1]) for x in words)]
            elif w.get("milestone") == "final":
                ms = [m for m in ms if "final" in m[1].lower()]
            return {"type": "deadline", "data": ms, "part": w.get("part")} if ms else None

        if "week" in w:
            week = sched.get(w["week"])
            if not week:
                return None
            ch = self.kb.topics.get(week.get("chapter", ""), {})
            return {"type": "week", "data": week, "chapter": ch}
        if "chapter" in w:
            ch = self.kb.topics.get(w["chapter"])
            weeks = ch.get("weeks") if ch else None
            return {"type": "chapter_weeks", "data": weeks, "chapter": ch} if weeks else None
        if "topic" in w:
            terms = self.topic_terms.get(w["topic"], [normalize(w["topic"])])
            weeks = [wk["week"] for wk in sched.values()
                     if any(_contains(normalize(" ".join(wk["topics"])), t) for t in terms)]
            if not weeks:
                weeks = sorted({x for c in self._chapters_for_topic(w["topic"])
                                for x in self.kb.topics[c].get("weeks", [])})
            return {"type": "topic_weeks", "data": weeks, "topic": w["topic"],
                    "label": self._topic_label(w["topic"])} if weeks else None
        rows = [(wk["week"], self.kb.topics.get(wk.get("chapter", ""), {}).get("title", wk.get("part", "")))
                for wk in sched.values()]
        return {"type": "schedule_overview", "data": rows} if rows else None

    # ---------------------------------------------------------------- topics
    def _chapters_for_topic(self, topic: str) -> list[str]:
        """
        Xếp hạng chương theo vị trí xuất hiện của chủ đề:
        keywords (3) > tiêu đề (2) > tiểu mục / tóm tắt (1). Chỉ giữ các chương có điểm cao nhất.
        """
        terms = self.topic_terms.get(topic, [normalize(topic.replace("_", " "))])
        scores = {}
        for ch_id, ch in self.kb.topics.items():
            kws = [normalize(k) for k in ch["keywords"]]
            title = normalize(ch["title"])
            body = normalize(ch["summary"] + " " + " ".join(ch["subtopics"]))
            score = 0
            for t in terms:
                if t in kws:
                    score = max(score, 3)
                elif _contains(title, t):
                    score = max(score, 2)
                elif _contains(body, t):
                    score = max(score, 1)
            if score:
                scores[ch_id] = score
        if not scores:
            return []
        top = max(scores.values())
        return sorted(c for c, sc in scores.items() if sc == top)

    def _topic_label(self, topic: str) -> str:
        """'SEMANTIC_GRAMMAR' -> 'semantic grammar', 'CFG' -> 'CFG (context-free grammar)'"""
        terms = self.topic_terms.get(topic)
        if not terms:
            return topic.replace("_", " ").lower()
        label = self.kb.lexicon_labels.get(topic, terms[0])
        if label.isupper() and len(terms) > 1:
            return f"{label} ({terms[1]})"
        return label

    def _exec_topics(self, p):
        w = p["where"]
        if "chapter_id" in w:
            ch = self.kb.topics.get(w["chapter_id"])
            if not ch:
                return None
            if p["select"] == "contains":
                text = self.kb.chapter_text(ch["id"])
                terms = self.topic_terms.get(p["check"], [normalize(p["check"])])
                found = any(_contains(text, t) for t in terms)
                evidence = [st for st in ch["subtopics"] + [ch["title"]]
                            if any(_contains(normalize(st), t) for t in terms)]
                return {"type": "chapter_check", "data": ch, "found": found, "evidence": evidence,
                        "label": self._topic_label(p["check"])}
            kind = "chapter_subtopics" if p["select"] == "subtopics" else "chapter_summary"
            return {"type": kind, "data": ch}
        if "topic" in w:
            chapters = [self.kb.topics[c] for c in self._chapters_for_topic(w["topic"])]
            return {"type": "topic_chapters", "data": chapters, "topic": w["topic"],
                    "label": self._topic_label(w["topic"])} if chapters else None
        chapters = list(self.kb.topics.values())
        return {"type": "chapter_list", "data": chapters} if chapters else None

    # ---------------------------------------------------------------- LO
    def _exec_learning_outcomes(self, p):
        w = p["where"]
        if "lo_id" not in w:
            data = {k: v for k, v in self.kb.los.items() if "." not in k}
            return {"type": "lo_list", "data": data} if data else None
        lo_id = w["lo_id"]
        desc = self.kb.los.get(lo_id)
        if not desc:
            return None
        chapters = [self.kb.topics[c] for c in LO_CHAPTERS.get(lo_id, []) if c in self.kb.topics]
        if p["select"] == "chapter" and not chapters:
            return None
        return {"type": "lo_chapter" if p["select"] == "chapter" else "lo",
                "lo": lo_id, "data": desc, "chapters": chapters}

    # ---------------------------------------------------------------- assignments
    def _find_part(self, topic: str) -> str | None:
        terms = self.topic_terms.get(topic, [normalize(topic)])
        for pid, part in self.kb.assignments.items():
            if not pid.startswith("PART_"):
                continue
            text = normalize(part["title"] + " " + " ".join(part["requirements"]))
            if any(_contains(text, t) for t in terms):
                return pid
        return None

    def _exec_assignments(self, p):
        w, a = p["where"], self.kb.assignments
        btl = a.get(w.get("assignment_id", "BTL01"))
        if "part" not in w:
            if not btl:
                return None
            parts = [a[x] for x in btl.get("parts", []) if x in a]
            return {"type": "assignment", "data": btl, "parts": parts}
        if w["part"] is None:
            # câu có/không mà không phần nào chứa chủ đề -> trả lời "không"
            return {"type": "assignment_check", "found": False, "data": None,
                    "label": self._topic_label(p["check"])}
        part = a.get(w["part"])
        if not part:
            return None
        if p["select"] == "outputs":
            return {"type": "part_outputs", "data": part} if part.get("outputs") else None
        if p["select"] == "contains":
            terms = self.topic_terms.get(p["check"], [normalize(p["check"])])
            text = normalize(part["title"] + " " + " ".join(part["requirements"]))
            return {"type": "assignment_check", "data": part, "label": self._topic_label(p["check"]),
                    "found": any(_contains(text, t) for t in terms)}
        return {"type": "part", "data": part}

    # ---------------------------------------------------------------- resources
    def _exec_resources(self, p):
        w, res = p["where"], list(self.kb.resources.values())
        if "type" in w:
            res = [r for r in res if r["type"] == w["type"]]
        if "usage" in w:
            phrase = w["usage"]
            words = [x for x in re.split(r"\W+", phrase) if x]

            def text(r):
                return normalize(r.get("usage", "") + " " + r.get("title", ""))

            exact = [r for r in res if _contains(text(r), phrase)]
            res = exact or [r for r in res if words and all(_contains(text(r), x) for x in words)]
            if not res:
                topic_key = self._norm_topic(phrase)
                chs = self._chapters_for_topic(topic_key) if topic_key else []
                if chs:
                    res = [r for r in self.kb.resources.values() if r["type"] == "textbook"]
                    return {"type": "resources", "data": res, "topic": phrase, "chapter": self.kb.topics.get(chs[0])}
        if not res:
            return None
        return {"type": "resources", "data": res, "topic": w.get("usage"),
                "chapter": self.kb.topics.get(w.get("chapter", ""))}

    # ---------------------------------------------------------------- regulations
    def _exec_regulations(self, p):
        rule = p["where"].get("rule")
        if rule is None:
            rules = {k: v for k, v in self.kb.regulations.items() if k != "OUT_OF_SCOPE"}
            return {"type": "rule_list", "data": rules} if rules else None
        content = self.kb.regulations.get(rule)
        return {"type": "rule", "rule": rule, "data": content} if content else None

    # ---------------------------------------------------------------- FAQ (dự phòng)
    def search_faq(self, sentence: str, threshold: float = 0.75) -> dict | None:
        """Tìm câu FAQ gần nhất theo độ trùng lặp từ (Jaccard); dùng khi tra cứu có cấu trúc thất bại."""
        q = set(re.findall(r"[\w.]+", normalize(sentence)))
        best, best_score = None, 0.0
        for item in self.kb.faq:
            f = set(re.findall(r"[\w.]+", normalize(item["question"])))
            score = len(q & f) / len(q | f) if q | f else 0.0
            if score > best_score:
                best, best_score = item, score
        if best and best_score >= threshold:
            return {"type": "faq", "data": best, "score": best_score,
                    "query": f"SELECT answer FROM faq WHERE id = '{best['id']}'"}
        return None
