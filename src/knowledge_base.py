"""
Phần II.3: Quản lý Cơ sở tri thức (Knowledge Base)
Phụ trách: Thành viên 3
Dữ liệu nguồn: các file trong data/ (course_info.txt, schedule.txt, topics.txt,...)
"""

class KnowledgeBase:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        # TODO: Đọc và lập chỉ mục các file dữ liệu trong data_dir
        self.course_info = {}
        self.schedule = {}
        self.topics = {}
        self.assignments = {}
        self.regulations = {}
        self.resources = {}

    def load_data(self):
        """Đọc và tổ chức dữ liệu thành cấu trúc tra cứu nhanh"""
        # TODO: Sinh viên cài đặt logic đọc dữ liệu từ data/
        pass
