"""
Mục 3.3: Xây dựng bộ phân tích cú pháp (Parser)
Phụ trách: Thành viên 3 (Mục 3.3)
Input: input/sentences.txt
Output: output/parse-results.txt (cây cú pháp dạng chuỗi ngoặc, hoặc '()' nếu không hợp lệ)
"""

class CourseParser:
    def __init__(self, grammar_path: str):
        self.grammar_path = grammar_path
        # TODO: Khởi tạo bộ Parser (ví dụ nltk.ChartParser / nltk.EarleyChartParser)

    def parse_sentence(self, sentence: str) -> str:
        """
        Phân tích cú pháp 1 câu tự nhiên.
        - Nếu câu hợp lệ: trả về chuỗi biểu diễn cây (ví dụ: '(S (Q_SCHEDULE ...))')
        - Nếu câu không hợp lệ hoặc lỗi OOV: trả về '()'
        """
        # TODO: Sinh viên cài đặt logic parse câu tại đây
        return "()"

    def process_file(self, input_path: str, output_path: str):
        """
        Đọc từng dòng từ input_path, gọi parse_sentence và ghi vào output_path.
        """
        # TODO: Đọc input/sentences.txt và ghi output/parse-results.txt
        pass
