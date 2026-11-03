"""
Phần II.3: Cơ sở tri thức (Knowledge Base)
Đọc và lập chỉ mục các file trong data/ (course_info, schedule, topics, assignments,
resources, regulations, faq) thành cấu trúc dict để QueryEngine tra cứu.

Mọi nội dung trả lời đều lấy từ các file dữ liệu; chỉ có 1 bảng bổ sung do nhóm tự viết là
LO_TO_CHAPTER (mỗi chuẩn đầu ra LO ứng với chương nào, suy từ nội dung đề cương).
"""
import os
import re

DEFAULT_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

# Chuẩn đầu ra chi tiết -> chương giảng dạy tương ứng (suy từ nội dung LO và 12 chương).
LO_TO_CHAPTER = {
    "LO1.1": "CH01", "LO2.1": "CH02", "LO2.2": "CH03", "LO2.3": "CH04", "LO2.4": "CH05",
    "LO2.5": "CH06", "LO3.1": "CH07", "LO3.2": "CH08", "LO3.3": "CH09", "LO3.4": "CH10",
    "LO4.1": "CH11", "LO4.2": "CH12",
}

_KEY_RE = re.compile(r"^([^\W\d][\w ]*):\s*(.*)$")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}


def _read_lines(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.rstrip("\n").rstrip("\r") for l in f]


def parse_fields(lines: list[str]) -> dict[str, list[str]]:
    """
    Đọc khối 'key: value' (value có thể nhiều dòng, danh sách '- item', dòng thụt lề là
    phần nối tiếp của dòng trước). Dòng trống kết thúc giá trị đang đọc.
    """
    fields: dict[str, list[str]] = {}
    key = None
    for raw in lines:
        if not raw.strip():
            key = None
            continue
        if re.fullmatch(r"[-=\s]+", raw) and not raw.strip().startswith("- "):
            continue
        m = _KEY_RE.match(raw) if not raw[0].isspace() else None
        if m:
            key = m.group(1).strip()
            fields[key] = [m.group(2).strip()] if m.group(2).strip() else []
        elif key is not None:
            if raw[0].isspace() and fields[key]:
                fields[key][-1] += " " + raw.strip()  # dòng nối tiếp
            else:
                fields[key].append(re.sub(r"^-\s+", "", raw.strip()))
    return fields


def _split_blocks(lines: list[str], header_re: re.Pattern):
    """Chia file thành các khối bắt đầu bằng dòng khớp header_re. Trả về [(match, [lines])]."""
    blocks, cur = [], None
    for line in lines:
        m = header_re.match(line)
        if m:
            cur = (m, [])
            blocks.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return blocks


def _title_case(text: str) -> str:
    small = {"And", "Of", "For", "The", "To", "In", "On", "With", "A"}
    words = text.title().split()
    return " ".join(w.lower() if (i and w in small) else w for i, w in enumerate(words))


class KnowledgeBase:
    def __init__(self, data_dir: str = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.course_info: dict = {}
        self.learning_outcomes: dict[str, str] = {}
        self.schedule: dict[str, dict] = {}
        self.topics: dict[str, dict] = {}
        self.assignments: dict = {}
        self.regulations: dict[str, str] = {}
        self.resources: list[dict] = []
        self.faq: list[dict] = []
        self.lo_to_chapter = dict(LO_TO_CHAPTER)
        self.load_data()

    # ------------------------------------------------------------------ loading
    def _path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)

    def load_data(self):
        self._load_course_info()
        self._load_schedule()
        self._load_topics()
        self._load_assignments()
        self._load_resources()
        self._load_regulations()
        self._load_faq()

    def _load_course_info(self):
        lines = _read_lines(self._path("course_info.txt"))
        f = parse_fields(lines)
        one = lambda k, d="": f.get(k, [d])[0] if f.get(k) else d
        info = {
            "course_id": one("course_id", "CO3085"),
            "course_name": one("course_name"),
            "course_name_en": one("course_name_en"),
            "semester": one("semester"),
            "credits": int(one("credits", "0") or 0),
            "ects": int(one("ects", "0") or 0),
            "format": one("format"),
            "total_hours": one("total_course_hours"),
            "lecture_hours": one("lecture_hours"),
            "assignment_hours": one("major_assignment_hours"),
            "self_study_hours": one("self_study_hours"),
            "description": " ".join(f.get("course_description", [])),
            "parts": f.get("main_parts", []),
            "assessment": {k: v[0] for k, v in f.items()
                           if k in ("class_attention_and_assignments", "major_assignment",
                                    "midterm_exam", "final_exam") and v},
            "exam_format": {k: f[k][0] for k in ("midterm", "final") if f.get(k)},
        }
        for exam, text in info["exam_format"].items():
            m = re.search(r"(\d+)\s*minutes", text)
            info[f"{exam}_minutes"] = int(m.group(1)) if m else None
        self.course_info = info
        for k in ("learning_outcomes", "detailed_learning_outcomes"):
            for item in f.get(k, []):
                m = re.match(r"(LO\d+(?:\.\d+)?)\s*-\s*(.*)", item)
                if m:
                    self.learning_outcomes[m.group(1)] = m.group(2).strip()

    def _load_schedule(self):
        lines = _read_lines(self._path("schedule.txt"))
        for m, body in _split_blocks(lines, re.compile(r"^WEEK\s+(\d+)\s*$")):
            f = parse_fields(body)
            week = int(m.group(1))
            ch = None
            if f.get("chapter"):
                cm = re.search(r"(\d+)", f["chapter"][0])
                ch = f"CH{int(cm.group(1)):02d}" if cm else None
            self.schedule[f"WEEK_{week:02d}"] = {
                "week": week, "part": f.get("part", [""])[0], "chapter": ch,
                "topics": f.get("topics", []),
                "activity": f.get("activity", [""])[0],
                "milestone": f.get("milestone", [""])[0],
            }

    def _load_topics(self):
        lines = _read_lines(self._path("topics.txt"))
        for m, body in _split_blocks(lines, re.compile(r"^CHAPTER\s+(\d+):\s*(.*)$")):
            f = parse_fields(body)
            cid = f.get("chapter_id", [f"CH{int(m.group(1)):02d}"])[0]
            self.topics[cid] = {
                "chapter_id": cid, "number": int(m.group(1)),
                "title": _title_case(m.group(2).strip()),
                "part": f.get("part", [""])[0],
                "keywords": [k.strip() for k in f.get("keywords", [""])[0].split(",") if k.strip()],
                "summary": " ".join(f.get("summary", [])),
                "subtopics": f.get("subtopics", []),
            }

    def _load_assignments(self):
        lines = _read_lines(self._path("assignments.txt"))
        header = re.compile(r"^(?:PART\s+(IV|III|II|I)\s*-\s*(.*)|(LLM/RAG EXTENSION))\s*$")
        top, sections, cur = [], [], None
        for line in lines:
            m = header.match(line)
            if m:
                cur = (m, [])
                sections.append(cur)
            elif cur is None:
                top.append(line)
            else:
                cur[1].append(line)
        f = parse_fields(top)
        a = {"assignment_id": f.get("assignment_id", ["BTL01"])[0],
             "title": f.get("title", [""])[0], "team_size": f.get("team_size", [""])[0],
             "domain": f.get("domain", [""])[0], "goal": " ".join(f.get("goal", [])),
             "parts": {}, "llm_rag": {}}
        for m, body in sections:
            sf = parse_fields(body)
            if m.group(3):
                a["llm_rag"] = {"status": sf.get("status", [""])[0],
                                "description": " ".join(sf.get("description", [])),
                                "not_required": sf.get("not_required", [])}
            else:
                pid = f"PART_{m.group(1)}"
                a["parts"][pid] = {
                    "id": pid, "title": m.group(2).strip(),
                    "requirements": sf.get("requirements", []) or sf.get("minimum_requirements", [])
                                    or sf.get("optional_or_extension", []),
                    "outputs": sf.get("suggested_outputs", []),
                    "intents": sf.get("suggested_intents", []),
                }
        self.assignments[a["assignment_id"]] = a

    def _load_resources(self):
        lines = _read_lines(self._path("resources.txt"))
        for m, body in _split_blocks(lines, re.compile(r"^(TEXTBOOK|REFERENCE)\s+(\d+)\s*$")):
            f = parse_fields(body)
            self.resources.append({
                "id": f"{m.group(1)} {m.group(2)}",
                "kind": "Giáo trình" if m.group(1) == "TEXTBOOK" else "Tài liệu tham khảo",
                "title": f.get("title", [""])[0],
                "author": (f.get("author") or f.get("authors") or [""])[0],
                "year": f.get("year", [""])[0],
                "usage": f.get("usage", [""])[0],
            })

    def _load_regulations(self):
        lines = _read_lines(self._path("regulations.txt"))
        f = parse_fields(lines[2:])  # bỏ tiêu đề
        for k, v in f.items():
            if k != "Lưu ý":
                self.regulations[k.upper()] = " ".join(v)

    def _load_faq(self):
        lines = _read_lines(self._path("faq.txt"))
        for m, body in _split_blocks(lines, re.compile(r"^Q(\d+):\s*$")):
            f = parse_fields(body)
            self.faq.append({"id": f"Q{m.group(1)}", "question": " ".join(f.get("question", [])),
                             "answer": " ".join(f.get("answer", []))})

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def chapter_number(chapter_id: str) -> int:
        return int(chapter_id[2:])

    def chapter_exists(self, chapter_id: str) -> bool:
        return chapter_id in self.topics

    def weeks_of_chapter(self, chapter_id: str) -> list[str]:
        return [w for w, d in self.schedule.items() if d["chapter"] == chapter_id]

    def find_chapters_for_terms(self, terms: list[str]) -> list[tuple[str, int]]:
        """
        Tìm các chương nói về một chủ đề: đếm số lần xuất hiện các thuật ngữ trong
        tiêu đề/keywords/subtopics (trọng số 2) và summary (trọng số 1). Trả về
        [(chapter_id, score)] giảm dần theo điểm, chỉ giữ chương có điểm >= 50% điểm cao nhất.
        """
        scores: dict[str, int] = {}
        for cid, ch in self.topics.items():
            strong = " ".join([ch["title"], " ".join(ch["keywords"]), " ".join(ch["subtopics"])]).lower()
            weak = ch["summary"].lower()
            sc = 0
            for t in terms:
                t = t.lower().strip()
                if not t:
                    continue
                stem = t[:-1] if t.endswith("s") and len(t) > 4 else t
                pat = re.compile(r"(?<!\w)" + re.escape(stem) + r"s?(?!\w)")
                sc += 2 * len(pat.findall(strong)) + len(pat.findall(weak))
            if sc:
                scores[cid] = sc
        if not scores:
            return []
        best = max(scores.values())
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(c, s) for c, s in ranked if s >= 0.5 * best]


if __name__ == "__main__":
    kb = KnowledgeBase()
    print("course:", kb.course_info["course_id"], kb.course_info["credits"], "tín chỉ,",
          kb.course_info["midterm_minutes"], "/", kb.course_info["final_minutes"], "phút")
    print("LO:", len(kb.learning_outcomes), "| weeks:", len(kb.schedule), "| chapters:", len(kb.topics),
          "| resources:", len(kb.resources), "| rules:", list(kb.regulations), "| faq:", len(kb.faq))
    print("assignment parts:", list(kb.assignments["BTL01"]["parts"]),
          kb.assignments["BTL01"]["parts"]["PART_I"]["outputs"])
