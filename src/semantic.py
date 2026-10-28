"""
Phần II.1: Xây dựng biểu diễn ngữ nghĩa (Semantic Representation)
Phụ trách: Thành viên 2
Output yêu cầu: output/semantic.txt (dạng logic/vị từ: GET_CREDIT(course=NLP), GET_DEADLINE(assignment=PROJECT)...)
"""

class SemanticInterpreter:
    def __init__(self):
        pass

    def interpret(self, sentence: str, parse_tree_str: str = "") -> str:
        """
        Ánh xạ câu hoặc cây cú pháp sang biểu diễn ngữ nghĩa dạng vị từ.
        """
        # TODO: Sinh viên cài đặt logic ánh xạ ngữ nghĩa tại đây
        return "GET_COURSE_INFO(target=CREDITS)"

    def process_file(self, input_path: str, output_path: str):
        """Đọc input/sentences.txt và xuất ra output/semantic.txt"""
        # TODO: Cài đặt đọc ghi file
        pass
