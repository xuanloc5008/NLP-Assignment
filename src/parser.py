"""
Mục 3.3: Xây dựng bộ phân tích cú pháp (Parser)
Input : input/sentences.txt (mỗi dòng 1 câu) + models/grammar.cfg
Output: output/parse-results.txt (mỗi dòng 1 kết quả, cùng thứ tự với input)
        - câu hợp lệ  : cây cú pháp dạng chuỗi ngoặc trên 1 dòng, vd '(S (Q_SCHEDULE tuần (WEEK_NUM 3) ...))'
        - câu không hợp lệ / ngoài văn phạm / có từ lạ (OOV): '()'

(Bản cài đặt do Lead Integrator bổ sung vì chưa có nhánh của Mục 3.3; Đức Anh có thể
 thay thế/cải tiến, miễn giữ nguyên giao diện CourseParser.)
"""
import os

from nltk.parse import ChartParser

from src.grammar_loader import DEFAULT_GRAMMAR_PATH, load_grammar
from src.tokenizer import VietnameseTokenizer


class CourseParser:
    def __init__(self, grammar_path: str = DEFAULT_GRAMMAR_PATH):
        self.grammar_path = grammar_path
        self.grammar = load_grammar(grammar_path)
        self.parser = ChartParser(self.grammar)
        self.tokenizer = VietnameseTokenizer(grammar_path)

    def parse_sentence(self, sentence: str) -> str:
        """Trả về cây dạng '(S ...)' trên 1 dòng, hoặc '()' nếu không parse được."""
        tokens = self.tokenizer.tokenize(sentence)
        if not tokens:
            return "()"
        try:
            tree = next(iter(self.parser.parse(tokens)), None)
        except ValueError:  # có token không thuộc từ điển của văn phạm (OOV)
            return "()"
        if tree is None:
            return "()"
        return " ".join(str(tree).split())

    def process_file(self, input_path: str, output_path: str):
        """Đọc từng dòng input_path, ghi kết quả tương ứng (cùng số dòng) vào output_path."""
        with open(input_path, "r", encoding="utf-8") as f:
            sentences = [line.rstrip("\n") for line in f]
        # bỏ các dòng trống ở cuối file để số dòng khớp số câu thật
        while sentences and not sentences[-1].strip():
            sentences.pop()

        results = [self.parse_sentence(s) for s in sentences]

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(r + "\n")
        ok = sum(r != "()" for r in results)
        print(f"[CourseParser] {ok}/{len(results)} câu parse được -> {output_path}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    CourseParser().process_file(os.path.join(root, "input", "sentences.txt"),
                                os.path.join(root, "output", "parse-results.txt"))
