"""
Phần II.4 & II.5: Truy xuất thông tin, Sinh câu trả lời tự nhiên & Xử lý Fallback
Phụ trách: Thành viên 3
Output yêu cầu: output/answer.txt
Yêu cầu Fallback: "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."
"""

class AnswerGenerator:
    FALLBACK_MESSAGE = "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."

    def __init__(self, query_engine):
        self.qe = query_engine

    def generate_answer(self, intent: str, entities: dict) -> str:
        """
        Dùng Template-based NLG để tạo câu trả lời tự nhiên từ kết quả truy vấn KB.
        Nếu ngoài miền hoặc không có dữ liệu, trả về self.FALLBACK_MESSAGE.
        """
        # TODO: Sinh viên cài đặt logic sinh câu trả lời tại đây
        return self.FALLBACK_MESSAGE
