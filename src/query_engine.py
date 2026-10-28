"""
Phần II.3: Xây dựng truy vấn tới Knowledge Base
Phụ trách: Thành viên 3
Output yêu cầu: output/query.txt
"""

class QueryEngine:
    def __init__(self, kb):
        self.kb = kb

    def build_query(self, intent: str, entities: dict) -> str:
        """
        Chuyển đổi (intent, entities) hoặc semantic representation thành câu truy vấn tương ứng.
        Ví dụ: "SELECT content FROM schedule WHERE week='WEEK_03'"
        """
        # TODO: Sinh viên cài đặt logic tạo câu truy vấn
        return "QUERY_COMMAND_HERE"

    def execute_query(self, intent: str, entities: dict) -> any:
        """
        Thực thi truy vấn trên đối tượng KnowledgeBase để lấy thông tin.
        """
        # TODO: Sinh viên cài đặt logic tra cứu dữ liệu
        return None
