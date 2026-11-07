"""
Nạp văn phạm CFG dùng chung cho Generator / Parser / Tokenizer.
Phụ trách: Xuân Lộc (Lead Integrator)

File models/grammar.cfg được viết tay (có dòng nối bằng '\\', dòng bắt đầu bằng '|',
terminal có khoảng trắng...) nên cần chuẩn hoá trước khi đưa cho nltk.CFG.fromstring.
Mọi module nên dùng load_grammar_text()/load_grammar() ở đây để cùng nhìn thấy 1 văn phạm.

Chuẩn hoá:
  - Bỏ dòng trống, comment '#'.
  - Nối dòng tiếp theo ('\\' cuối dòng hoặc dòng bắt đầu bằng '|') vào luật đang viết.
  - Terminal có khoảng trắng bên trong ('word sense disambiguation') -> dùng '_'.
  - Đảm bảo ký hiệu S dẫn tới mọi nhóm câu hỏi Q_* đã định nghĩa (Q_LO, Q_CONTEXT...).
"""
import os
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_GRAMMAR_PATH = os.path.join(PROJECT_ROOT, "models", "grammar.cfg")

_TERMINAL_RE = re.compile(r"'([^']*)'")


def _join_continuations(raw: str) -> list[str]:
    rules: list[str] = []
    current = ""
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            line = line[:-1].strip()
        if "->" in line:
            if current:
                rules.append(current)
            current = line
        else:  # dòng nối tiếp (bắt đầu bằng '|' hoặc thiếu '|')
            current += " " + (line if line.startswith("|") else "| " + line)
    if current:
        rules.append(current)
    return rules


def load_grammar_text(path: str = DEFAULT_GRAMMAR_PATH) -> str:
    """Trả về chuỗi văn phạm đã chuẩn hoá, sẵn sàng cho nltk.CFG.fromstring."""
    with open(path, "r", encoding="utf-8") as f:
        rules = _join_continuations(f.read())

    # Terminal có khoảng trắng -> gạch dưới
    rules = [_TERMINAL_RE.sub(lambda m: "'" + m.group(1).strip().replace(" ", "_") + "'", r)
             for r in rules]

    # Đảm bảo S bao phủ mọi Q_* đã định nghĩa
    lhs_all = [r.split("->", 1)[0].strip() for r in rules]
    q_symbols = [s for s in dict.fromkeys(lhs_all) if s.startswith("Q_")]
    for i, r in enumerate(rules):
        if r.split("->", 1)[0].strip() == "S":
            present = set(re.findall(r"[A-Za-z_]+", r.split("->", 1)[1]))
            missing = [q for q in q_symbols if q not in present]
            if missing:
                rules[i] = r + " | " + " | ".join(missing)
    return "\n".join(rules)


def load_grammar(path: str = DEFAULT_GRAMMAR_PATH):
    """Trả về đối tượng nltk.CFG."""
    from nltk.grammar import CFG
    return CFG.fromstring(load_grammar_text(path))


def grammar_terminals(path: str = DEFAULT_GRAMMAR_PATH) -> set[str]:
    """Tập mọi terminal xuất hiện trong văn phạm (đã chuẩn hoá)."""
    text = load_grammar_text(path)
    return set(_TERMINAL_RE.findall(text))
