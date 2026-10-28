"""
Phần IV: Đánh giá hệ thống (Evaluation)
Phụ trách: Thành viên 4
Dữ liệu nguồn: data/sample_queries.txt và các câu kiểm thử mở rộng
Output yêu cầu: output/evaluation.txt (độ chính xác, phân tích lỗi, ưu/nhược điểm)
"""

class SystemEvaluator:
    def __init__(self, detector, parser, query_engine, nlg):
        self.detector = detector
        self.parser = parser
        self.qe = query_engine
        self.nlg = nlg

    def evaluate(self, sample_queries_path: str, output_path: str):
        """
        Chạy tập kiểm thử, so khớp kết quả dự đoán với nhãn kỳ vọng
        và xuất báo cáo đánh giá hoàn chỉnh ra output_path.
        """
        # TODO: Sinh viên cài đặt logic tính Accuracy, Confusion Matrix và xuất báo cáo
        pass
