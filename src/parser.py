"""
Mục 3.3: Xây dựng bộ phân tích cú pháp (Parser)
Phụ trách: Thành viên 3 (Mục 3.3)
Input: input/sentences.txt
Output: output/parse-results.txt (cây cú pháp dạng chuỗi ngoặc, hoặc '()' nếu không hợp lệ)
"""
import os
import re
import sys
import unicodedata

import nltk

EMPTY_TREE = "()"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_GRAMMAR_PATH = os.path.join(PROJECT_ROOT, "models", "grammar.cfg")

# Dấu câu bị loại bỏ khi tách token (giữ lại '.' bên trong token, ví dụ 'lo2.5')
_PUNCT_RE = re.compile(r"[?!,;:\"'()\[\]{}…]")
# 'L.O.2.5' / 'LO 2.5' / 'lo2.5' -> 'lo2.5'
_LO_RE = re.compile(r"\bl\.?\s*o\.?\s*(\d+)\.(\d+)")


class CourseParser:
    def __init__(self, grammar_path: str = DEFAULT_GRAMMAR_PATH):
        self.grammar_path = grammar_path
        with open(grammar_path, encoding="utf-8") as f:
            text = unicodedata.normalize("NFC", f.read())
        self.grammar = nltk.CFG.fromstring(text)
        self.parser = nltk.ChartParser(self.grammar)

        # Tập từ vựng (terminal) của văn phạm, dùng để kiểm tra OOV
        self.terminals = {
            sym
            for prod in self.grammar.productions()
            for sym in prod.rhs()
            if isinstance(sym, str)
        }
        # Từ ghép trong văn phạm ('bài_tập_lớn' -> ('bài', 'tập', 'lớn')) để gộp token
        self.compounds = {
            tuple(term.split("_")): term for term in self.terminals if "_" in term
        }
        self.max_compound_len = max((len(k) for k in self.compounds), default=1)

    def tokenize(self, sentence: str) -> list[str]:
        """
        Chuẩn hoá câu (NFC, chữ thường, bỏ dấu câu) và gộp từ ghép theo
        chiến lược khớp dài nhất (longest match) dựa trên từ vựng của văn phạm.
        """
        text = unicodedata.normalize("NFC", sentence).lower().strip()
        text = _LO_RE.sub(r"lo\1.\2", text)
        text = text.replace("/", " ")
        text = _PUNCT_RE.sub(" ", text)

        words = []
        for w in text.split():
            w = w.strip(".")
            if w:
                words.append(w)

        tokens = []
        i = 0
        while i < len(words):
            for n in range(min(self.max_compound_len, len(words) - i), 1, -1):
                key = tuple(words[i:i + n])
                if key in self.compounds:
                    tokens.append(self.compounds[key])
                    i += n
                    break
            else:
                tokens.append(words[i])
                i += 1
        return tokens

    def parse_tree(self, sentence: str):
        """Trả về cây nltk.Tree đầu tiên, hoặc None nếu câu không thuộc văn phạm."""
        tokens = self.tokenize(sentence)
        if not tokens or any(t not in self.terminals for t in tokens):
            return None
        try:
            return next(self.parser.parse(tokens), None)
        except ValueError:
            return None

    def parse_sentence(self, sentence: str) -> str:
        """
        Phân tích cú pháp 1 câu tự nhiên.
        - Nếu câu hợp lệ: trả về chuỗi biểu diễn cây (ví dụ: '(S (Q_SCHEDULE ...))')
        - Nếu câu không hợp lệ hoặc lỗi OOV: trả về '()'
        """
        tree = self.parse_tree(sentence)
        if tree is None:
            return EMPTY_TREE
        return tree.pformat(margin=sys.maxsize)

    def process_file(self, input_path: str, output_path: str):
        """
        Đọc từng dòng từ input_path, gọi parse_sentence và ghi vào output_path.
        Mỗi dòng input tương ứng đúng một dòng output.
        """
        with open(input_path, encoding="utf-8") as f:
            sentences = f.read().splitlines()

        results = [self.parse_sentence(s) for s in sentences]

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(r + "\n")

        n_ok = sum(r != EMPTY_TREE for r in results)
        print(f"-> Đã phân tích {n_ok}/{len(results)} câu hợp lệ, ghi vào {output_path}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    parser = CourseParser(os.path.join(root, "models", "grammar.cfg"))
    parser.process_file(
        os.path.join(root, "input", "sentences.txt"),
        os.path.join(root, "output", "parse-results.txt"),
    )
