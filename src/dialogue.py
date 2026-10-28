"""
Phần III: Xử lý ngữ cảnh hội thoại cục bộ (Local Discourse Context)
Phụ trách: Thành viên 4
Dữ liệu nguồn: data/dialogues.txt
Output yêu cầu: output/dialogue.txt (thể hiện 4 trường: hội thoại vào, ngữ cảnh dùng, diễn giải, câu trả lời)
"""

class DialogueManager:
    def __init__(self, detector, query_engine, nlg):
        self.detector = detector
        self.qe = query_engine
        self.nlg = nlg
        # TODO: Lưu trạng thái ngữ cảnh hội thoại (DialogueState)

    def process_dialogues(self, input_path: str, output_path: str):
        """
        Đọc các đoạn hội thoại nhiều lượt từ input_path,
        giải quyết quan hệ tham chiếu (anaphora: 'nó', 'chương này', 'phần này',...)
        và xuất báo cáo ra output_path.
        """
        # TODO: Sinh viên cài đặt logic xử lý tham chiếu ngữ cảnh tại đây
        pass
