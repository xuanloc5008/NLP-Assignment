"""
Phần II.2: Nhận diện Intent và Entity
Phụ trách: Thành viên 2
Output yêu cầu: output/intent-entity.txt
Phương pháp: Rule-based, keyword matching hoặc mô hình thống kê (TF-IDF + ML).
"""

class IntentEntityDetector:
    def __init__(self):
        # TODO: Khởi tạo từ điển thực thể entities.txt hoặc load model
        pass

    def detect(self, sentence: str) -> tuple[str, dict]:
        """
        Nhận vào câu tự nhiên, trả về (intent, dict_entities).
        Ví dụ: ('GET_SCHEDULE', {'week': 'WEEK_03'})
        """
        # TODO: Sinh viên cài đặt logic phân loại intent và trích xuất entity
        intent = "UNKNOWN"
        entities = {}
        return intent, entities

    def process_file(self, input_path: str, output_path: str):
        """Đọc input/sentences.txt và xuất ra output/intent-entity.txt"""
        # TODO: Cài đặt đọc ghi file
        pass
