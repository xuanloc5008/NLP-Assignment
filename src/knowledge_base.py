"""
Mục 4.1.3: Quản lý Cơ sở tri thức (Knowledge Base)
Phụ trách: Đức Anh
Dữ liệu nguồn: các file trong data/ (course_info.txt, schedule.txt, topics.txt,...)

Mỗi file văn bản bán cấu trúc được đọc và lập chỉ mục thành các bảng (dict):
    course_info  : {'credits': '3', 'midterm': 'open-book, written, 60 minutes', ...}
    los          : {'LO2.5': 'Kiến thức xác suất ...', ...}
    schedule     : {'WEEK_03': {'week': 3, 'chapter': 'CH03', 'topics': [...], ...}}
    topics       : {'CH03': {'title': ..., 'keywords': [...], 'summary': ..., 'subtopics': [...]}}
    assignments  : {'BTL01': {...}, 'PART_I': {...}, 'PART_II': {...}, ...}
    regulations  : {'AI_USAGE': '...', 'LLM_RAG': '...', ...}
    resources    : {'TEXTBOOK_1': {'title': ..., 'usage': ...}, ...}
    faq          : [{'question': ..., 'answer': ...}, ...]
    lexicon      : {'CFG': ['cfg', 'context-free grammar'], ...}   (mục TOPICS của entities.txt)
"""
import os
import re
import unicodedata

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Dòng 'key: value' (key không chứa khoảng trắng, ví dụ 'credits: 3', 'AI_usage:')
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
# 'LO2.5 - Kiến thức ...'
_LO_RE = re.compile(r"^(LO\d+(?:\.\d+)?)\s*-\s*(.*)$")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}

# Ánh xạ chuẩn đầu ra chi tiết -> chương theo cấu trúc đề cương CO3085
# (mỗi LO chi tiết ứng với một chương trong topics.txt, ví dụ LO2.5 -> Chương 6).
LO_CHAPTERS = {
    "LO1.1": ["CH01"],
    "LO2.1": ["CH02"], "LO2.2": ["CH03"], "LO2.3": ["CH04"],
    "LO2.4": ["CH05"], "LO2.5": ["CH06"],
    "LO3.1": ["CH07"], "LO3.2": ["CH08"], "LO3.3": ["CH09"], "LO3.4": ["CH10"],
    "LO4.1": ["CH11"], "LO4.2": ["CH12"],
}


def normalize(text: str) -> str:
    """Chuẩn hoá NFC + chữ thường + gọn khoảng trắng (dùng để so khớp chuỗi)."""
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text.lower()).strip()


def _read(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return unicodedata.normalize("NFC", f.read()).splitlines()


def _title_case(text: str) -> str:
    """'FEATURES AND AUGMENTED GRAMMAR' -> 'Features and Augmented Grammar'"""
    small = {"and", "of", "for", "to", "the", "a", "an"}
    words = text.strip().lower().split()
    return " ".join(w if i and w in small else w[:1].upper() + w[1:] for i, w in enumerate(words))


def _join(lines: list[str]) -> str:
    return " ".join(l.strip() for l in lines if l.strip())


class KnowledgeBase:
    def __init__(self, data_dir: str = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.course_info = {}
        self.los = {}
        self.schedule = {}
        self.topics = {}
        self.assignments = {}
        self.regulations = {}
        self.resources = {}
        self.faq = []
        self.lexicon = {}
        self.lexicon_labels = {}

    def _path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)

    def load_data(self):
        """Đọc và tổ chức dữ liệu thành cấu trúc tra cứu nhanh"""
        loaders = [
            ("course_info.txt", self._load_course_info),
            ("schedule.txt", self._load_schedule),
            ("topics.txt", self._load_topics),
            ("assignments.txt", self._load_assignments),
            ("regulations.txt", self._load_regulations),
            ("resources.txt", self._load_resources),
            ("faq.txt", self._load_faq),
            ("entities.txt", self._load_entities),
        ]
        for name, loader in loaders:
            if os.path.exists(self._path(name)):
                loader(_read(self._path(name)))
        # Liên kết chương -> các tuần học (dùng cho câu "Chương 4 học vào tuần nào?")
        for week_id, week in self.schedule.items():
            ch = week.get("chapter")
            if ch in self.topics:
                self.topics[ch].setdefault("weeks", []).append(week["week"])
        return self

    # ------------------------------------------------------------ course_info
    def _load_course_info(self, lines: list[str]):
        """
        Khối 'key: value' một dòng, khối 'key:' nhiều dòng (course_description,
        main_parts, learning_outcomes, assessment, exam_format...).
        """
        info, key, block = {}, None, []

        def flush():
            if key is not None:
                info[key] = block[:]

        for line in lines[2:]:
            m = _KV_RE.match(line)
            if m and not line.startswith(" "):
                flush()
                key, value = m.group(1).lower(), m.group(2).strip()
                if value:
                    info[key] = value
                    key, block = None, []
                else:
                    block = []
            elif key is not None:
                block.append(line)
        flush()

        # Tách các khối nhiều dòng thành cấu trúc
        info["course_description"] = _join(info.get("course_description", []))
        info["main_parts"] = [l.strip() for l in info.get("main_parts", []) if l.strip()]
        for k in ("learning_outcomes", "detailed_learning_outcomes"):
            self.los.update(self._parse_los(info.pop(k, [])))
        # 'assessment:' / 'exam_format:' chỉ là tiêu đề nhóm, các dòng con đã là key riêng
        info.pop("assessment", None)
        info.pop("exam_format", None)
        self.course_info = info

    @staticmethod
    def _parse_los(lines: list[str]) -> dict:
        los, cur = {}, None
        for l in lines:
            m = _LO_RE.match(l.strip())
            if m:
                cur = m.group(1)
                los[cur] = m.group(2).strip()
            elif cur and l.strip():
                los[cur] += " " + l.strip()
        return los

    # --------------------------------------------------------------- schedule
    def _load_schedule(self, lines: list[str]):
        cur = None
        for line in lines:
            m = re.match(r"^WEEK\s+(\d+)\s*$", line.strip())
            if m:
                n = int(m.group(1))
                cur = {"week": n, "topics": []}
                self.schedule[f"WEEK_{n:02d}"] = cur
                continue
            if cur is None:
                continue
            if line.startswith("- "):
                cur["topics"].append(line[2:].strip())
                continue
            kv = _KV_RE.match(line)
            if kv and kv.group(2):
                k, v = kv.group(1), kv.group(2).strip()
                if k == "chapter":
                    num = re.search(r"\d+", v)
                    cur["chapter"] = f"CH{int(num.group()):02d}" if num else v
                else:
                    cur[k] = v

    # ----------------------------------------------------------------- topics
    def _load_topics(self, lines: list[str]):
        cur, mode = None, None
        for line in lines:
            s = line.strip()
            m = re.match(r"^CHAPTER\s+(\d+)\s*:\s*(.+)$", s)
            if m:
                ch = f"CH{int(m.group(1)):02d}"
                cur = {"id": ch, "number": int(m.group(1)), "title": _title_case(m.group(2)),
                       "keywords": [], "summary": "", "subtopics": []}
                self.topics[ch] = cur
                mode = None
                continue
            if cur is None or not s:
                continue
            kv = _KV_RE.match(s)
            if kv:
                k, v = kv.group(1), kv.group(2).strip()
                if k == "keywords":
                    cur["keywords"] = [w.strip() for w in v.split(",") if w.strip()]
                elif k in ("summary", "subtopics"):
                    mode = k
                elif k != "chapter_id":
                    cur[k] = v
                continue
            if mode == "summary":
                cur["summary"] = (cur["summary"] + " " + s).strip()
            elif mode == "subtopics":
                cur["subtopics"].append(s)

    # ------------------------------------------------------------ assignments
    def _load_assignments(self, lines: list[str]):
        """
        BTL01 (thông tin chung) và các phần PART_I..PART_IV.
        Mỗi phần gồm tiêu đề, trạng thái và danh sách yêu cầu / output gợi ý.
        """
        btl = {"parts": []}
        cur, key = btl, None
        for line in lines:
            s = line.strip()
            m = re.match(r"^PART\s+([IVX]+)\s*-\s*(.+)$", s)
            if m:
                pid = f"PART_{m.group(1)}"
                cur = {"id": pid, "number": _ROMAN.get(m.group(1), 0),
                       "title": m.group(2).strip(), "requirements": [], "outputs": []}
                self.assignments[pid] = cur
                btl["parts"].append(pid)
                key = None
                continue
            if s.startswith("LLM/RAG EXTENSION"):
                cur = {"id": "LLM_RAG_EXTENSION", "title": "LLM/RAG Extension",
                       "requirements": [], "outputs": []}
                self.assignments[cur["id"]] = cur
                key = None
                continue
            if not s or set(s) <= {"-", "="}:
                continue
            kv = _KV_RE.match(s)
            if kv:
                k, v = kv.group(1), kv.group(2).strip()
                if v:
                    cur[k] = v
                    key = None
                else:
                    key = k
                continue
            if key is None:
                continue
            if s.startswith("- "):
                item = s[2:].strip()
                target = "not_required" if key == "not_required" else "requirements"
                cur.setdefault(target, []).append(item)
            elif key == "suggested_outputs":
                cur["outputs"].append(os.path.basename(s))
            elif key == "suggested_intents":
                cur.setdefault("intents", []).append(s)
            else:
                cur[key] = (cur.get(key, "") + " " + s).strip()
        if "assignment_id" in btl:
            self.assignments[btl.pop("assignment_id")] = btl

    # ------------------------------------------------------------ regulations
    def _load_regulations(self, lines: list[str]):
        key = None
        for line in lines:
            s = line.strip()
            kv = _KV_RE.match(s)
            if kv and not kv.group(2):
                key = kv.group(1).upper()
                self.regulations[key] = ""
            elif key and s:
                self.regulations[key] = (self.regulations[key] + " " + s).strip()

    # -------------------------------------------------------------- resources
    def _load_resources(self, lines: list[str]):
        cur = None
        for line in lines:
            s = line.strip()
            m = re.match(r"^(TEXTBOOK|REFERENCE)\s+(\d+)$", s)
            if m:
                cur = {"id": f"{m.group(1)}_{m.group(2)}", "type": m.group(1).lower()}
                self.resources[cur["id"]] = cur
                continue
            kv = _KV_RE.match(s)
            if kv and cur is not None and kv.group(2):
                k, v = kv.group(1), kv.group(2).strip()
                cur["authors" if k == "author" else k] = v
            elif kv and kv.group(1) == "study_note":
                cur = None
                self.course_info["study_note"] = ""
            elif s and "study_note" in self.course_info and cur is None:
                self.course_info["study_note"] = (self.course_info["study_note"] + " " + s).strip()

    # -------------------------------------------------------------------- faq
    def _load_faq(self, lines: list[str]):
        cur, key = None, None
        for line in lines:
            s = line.strip()
            if re.match(r"^Q\d+:$", s):
                cur = {"id": s[:-1], "question": "", "answer": ""}
                self.faq.append(cur)
                continue
            if cur is None or not s:
                continue
            kv = _KV_RE.match(s)
            if kv and kv.group(1) in ("question", "answer"):
                key = kv.group(1)
                cur[key] = kv.group(2).strip()
            elif key:
                cur[key] += " " + s

    # --------------------------------------------------------------- entities
    def _load_entities(self, lines: list[str]):
        """Mục TOPICS: 'POS Tagging = gán nhãn từ loại' -> lexicon['POS_TAGGING'] = [...]"""
        section = None
        for line in lines:
            s = line.strip()
            if re.fullmatch(r"[A-Z]+", s):
                section = s
                continue
            if section != "TOPICS" or "=" not in s:
                continue
            en, vi = (x.strip() for x in s.split("=", 1))
            key = re.sub(r"\W+", "_", en.upper()).strip("_")
            terms = [normalize(en)] + [normalize(v) for v in vi.split("/") if v.strip()]
            self.lexicon[key] = list(dict.fromkeys(terms))
            self.lexicon_labels[key] = en

    # ---------------------------------------------------------- tra cứu tiện ích
    def chapter_text(self, ch_id: str) -> str:
        """Toàn bộ nội dung văn bản của một chương (dùng cho tìm kiếm từ khoá)."""
        ch = self.topics.get(ch_id, {})
        weeks = [w for w in self.schedule.values() if w.get("chapter") == ch_id]
        parts = [ch.get("title", ""), ", ".join(ch.get("keywords", [])), ch.get("summary", ""),
                 " ".join(ch.get("subtopics", []))] + [" ".join(w["topics"]) for w in weeks]
        return normalize(" ".join(parts))

    def stats(self) -> dict:
        return {
            "course_info": len(self.course_info), "los": len(self.los),
            "schedule": len(self.schedule), "topics": len(self.topics),
            "assignments": len(self.assignments), "regulations": len(self.regulations),
            "resources": len(self.resources), "faq": len(self.faq),
            "lexicon": len(self.lexicon),
        }


if __name__ == "__main__":
    kb = KnowledgeBase().load_data()
    print(kb.stats())
