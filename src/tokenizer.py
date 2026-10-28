"""
Mô-đun Tiền xử lý & Tokenizer tiếng Việt
Phụ trách: Thành viên 4 (Lead Integrator) / Thành viên 1
"""

class VietnameseTokenizer:
    def __init__(self):
        # TODO: Định nghĩa danh sách từ ghép và các cụm thực thể cần gộp token
        self.compound_words = []

    def tokenize(self, text: str) -> list[str]:
        """
        Nhận vào chuỗi câu tự nhiên, chuẩn hoá chữ thường, xoá dấu câu
        và tách thành danh sách các token.
        """
        # TODO: Sinh viên cài đặt logic tách từ tại đây
        return text.lower().strip().split()

    def detokenize(self, tokens: list[str]) -> str:
        """
        Chuyển danh sách token thành câu tự nhiên hoàn chỉnh.
        """
        # TODO: Sinh viên cài đặt logic nối từ tại đây
        return " ".join(tokens)
