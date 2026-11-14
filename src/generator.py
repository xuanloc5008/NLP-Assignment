"""
Mục 3.2: Viết giải thuật sinh câu hợp lệ từ văn phạm CFG
Phụ trách: Thành viên 2 (Mục 3.2)
Output yêu cầu: output/samples.txt (tối đa 10.000 câu, mỗi dòng 1 câu)
"""

import os
import re
from nltk.grammar import CFG
from nltk.parse.generate import generate

class SentenceGenerator:
    def __init__(self, grammar_path: str):
        self.grammar_path = grammar_path
        self.grammar = None
        self._load_grammar()

    def _load_grammar(self):
        r"""
        Đọc và tiền xử lý file văn phạm CFG:
        - Bỏ qua các dòng trống và dòng chú thích (#).
        - Ghép nối các dòng bị ngắt bởi dấu `\` hoặc bắt đầu bằng `|`.
        - Sửa lỗi thiếu ngoặc kép cho một số cụm từ.
        """
        try:
            with open(self.grammar_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            processed_lines = []
            current_rule = ""

            for line in lines:
                line = line.strip()
                # Bỏ qua dòng trống hoặc comment
                if not line or line.startswith('#'):
                    continue

                # Xóa ký tự \ ở cuối dòng 
                if line.endswith('\\'):
                    line = line[:-1].strip()

                # Nếu dòng bắt đầu bằng S ->, Q_..., hoặc các ký hiệu viết hoa -> luật mới
                if "->" in line:
                    if current_rule:
                        processed_lines.append(current_rule)
                    current_rule = line
                # Nếu dòng bắt đầu bằng |, ghép nối vào luật hiện tại
                elif line.startswith('|'):
                    current_rule += " " + line
                else:
                    # thêm các trường hợp rớt dòng không có dấu |
                    current_rule += " | " + line

            if current_rule:
                processed_lines.append(current_rule)

            # Cập nhật luật S để bao gồm Q_LO và Q_CONTEXT
            for i, rule in enumerate(processed_lines):
                if rule.startswith("S ->"):
                    if "Q_LO" not in rule:
                        processed_lines[i] += " | Q_LO"
                    if "Q_CONTEXT" not in rule:
                        processed_lines[i] += " | Q_CONTEXT"

            grammar_str = "\n".join(processed_lines)
            
            # Khắc phục lỗi chuỗi có khoảng trắng không được thay thế bằng gạch dưới
            grammar_str = grammar_str.replace("'word sense disambiguation'", "'word_sense_disambiguation'")
            
            self.grammar = CFG.fromstring(grammar_str)
            print(f"[SentenceGenerator] Đã nạp thành công văn phạm từ: {self.grammar_path}")
        except Exception as e:
            print(f"[Lỗi] Không thể nạp văn phạm từ {self.grammar_path}: {e}")

    def generate(self, max_samples: int = 10000, max_depth: int = 8) -> list[str]:
        """
        Duyệt sinh câu bằng NLTK generate, cân bằng qua tất cả các nhánh Intent dưới S
        và giới hạn tối đa max_samples câu không trùng lặp.
        """
        from nltk.grammar import Nonterminal

        samples = []
        seen = set()
        if not self.grammar:
            print("[Lỗi] Văn phạm chưa được khởi tạo.")
            return samples

        try:
            s_prods = self.grammar.productions(lhs=self.grammar.start())
            branches = [p.rhs()[0] for p in s_prods if len(p.rhs()) == 1 and isinstance(p.rhs()[0], Nonterminal)]
            if not branches:
                branches = [self.grammar.start()]

            per_branch_quota = max(500, max_samples // len(branches))
            # Vòng 1: lấy mẫu đều trên từng nhánh Intent để đảm bảo đủ mọi loại câu hỏi
            for br in branches:
                count = 0
                for sentence_tokens in generate(self.grammar, start=br, n=per_branch_quota * 2, depth=max_depth):
                    sentence = " ".join(sentence_tokens).replace('_', ' ')
                    if sentence not in seen:
                        seen.add(sentence)
                        samples.append(sentence)
                        count += 1
                        if count >= per_branch_quota or len(samples) >= max_samples:
                            break
                if len(samples) >= max_samples:
                    break

            # Vòng 2: nếu chưa chạm ngưỡng max_samples thì lấy thêm từ toàn bộ văn phạm
            if len(samples) < max_samples:
                for sentence_tokens in generate(self.grammar, n=max_samples * 2, depth=max_depth):
                    sentence = " ".join(sentence_tokens).replace('_', ' ')
                    if sentence not in seen:
                        seen.add(sentence)
                        samples.append(sentence)
                        if len(samples) >= max_samples:
                            break
        except Exception as e:
            print(f"[Lỗi] Xảy ra lỗi trong quá trình sinh câu: {e}")
            
        return samples

    def save_samples(self, output_path: str, max_samples: int = 10000):
        """Lưu kết quả sinh câu ra file .txt"""
        samples = self.generate(max_samples=max_samples)
        
        if not samples:
            print("[Cảnh báo] Không có câu nào được sinh ra để lưu.")
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for sentence in samples:
                    f.write(sentence + "\n")
            print(f"[Thành công] Đã lưu {len(samples)} câu sinh từ CFG vào '{output_path}'.")
        except Exception as e:
            print(f"[Lỗi] Không thể ghi file {output_path}: {e}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    grammar_file = os.path.join(project_root, "models", "grammar.cfg")
    output_file = os.path.join(project_root, "output", "samples.txt")
    
    print("="*60)
    print("KIỂM THỬ ĐỘC LẬP PHẦN 3.2 - SINH CÂU TỪ CFG")
    print("="*60)
    
    generator = SentenceGenerator(grammar_file)
    generator.save_samples(output_file, max_samples=10000)
