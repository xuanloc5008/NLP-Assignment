"""
Mục 3.2: Viết giải thuật sinh câu hợp lệ từ văn phạm CFG
Phụ trách: Thành viên 2 (Mục 3.2)
Output yêu cầu: output/samples.txt (tối đa 10.000 câu, mỗi dòng 1 câu)
"""

class SentenceGenerator:
    def __init__(self, grammar_path: str):
        self.grammar_path = grammar_path
        # TODO: Đọc tập luật văn phạm từ self.grammar_path

    def generate(self, max_samples: int = 10000, max_depth: int = 10) -> list[str]:
        """
        Thuật toán duyệt sinh câu (BFS / DFS / NLTK generate)
        từ ký hiệu bắt đầu S.
        """
        # TODO: Sinh viên cài đặt giải thuật sinh câu hợp lệ tại đây
        samples = []
        return samples

    def save_samples(self, output_path: str, max_samples: int = 10000):
        """Lưu danh sách câu sinh được vào output_path"""
        # TODO: Sinh viên xuất kết quả ra file theo quy định
        pass
