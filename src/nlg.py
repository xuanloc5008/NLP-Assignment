"""
Phần II.4 & II.5: Truy xuất thông tin, Sinh câu trả lời tự nhiên (Template-based NLG)
và Xử lý Fallback cho trường hợp ngoài phạm vi / không tìm thấy thông tin.
Output: output/answer.txt
"""
from src.query_engine import QueryEngine

class AnswerGenerator:
    FALLBACK_MESSAGE = "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."

    def __init__(self, query_engine: QueryEngine):
        self.qe = query_engine

    def generate_answer(self, intent: str, entities: dict) -> str:
        """
        Sinh câu trả lời tự nhiên từ kết quả truy vấn Knowledge Base.
        Nếu là câu ngoài phạm vi hoặc không tìm thấy dữ liệu -> trả về FALLBACK_MESSAGE.
        """
        if intent == "UNKNOWN" or entities.get("scope") == "OUT_OF_SCOPE":
            return self.FALLBACK_MESSAGE

        if intent == "CONTEXT_DEPENDENT":
            # Nếu chạy ở chế độ câu đơn không có ngữ cảnh, fallback hoặc yêu cầu ngữ cảnh
            return self.FALLBACK_MESSAGE

        data = self.qe.execute_query(intent, entities)
        if data is None:
            return self.FALLBACK_MESSAGE

        # 1. GET_COURSE_INFO
        if intent == "GET_COURSE_INFO":
            if entities.get("metric") == "CREDITS":
                return f"Môn học {data.get('course_name', 'Xử lý Ngôn ngữ Tự nhiên')} ({data.get('course_id', 'CO3085')}) có {data.get('credits', 3)} tín chỉ (tương đương {data.get('ects', 6)} tín chỉ ECTS)."
            if entities.get("metric") == "PARTS":
                parts = ", ".join(data) if isinstance(data, list) else str(data)
                return f"Môn học gồm 3 phần chính: {parts}."
            if "exam" in entities:
                return f"Thời gian làm bài thi {data.get('exam')} là {data.get('minutes')} phút theo đề cương môn học."

        # 2. GET_SCHEDULE
        elif intent == "GET_SCHEDULE":
            if "week" in entities:
                w_info = data
                topics = ", ".join(w_info.get("topics", []))
                ch = w_info.get("chapter", "")
                return f"Tuần {w_info.get('week')} học về {ch}: {topics}."
            if "chapter" in entities:
                weeks = ", ".join(data.get("weeks", []))
                return f"{data.get('chapter')} ({data.get('title')}) được giảng dạy vào {weeks}."

        # 3. GET_TOPIC
        elif intent == "GET_TOPIC":
            if "topic" in entities:
                ch_list = ", ".join(data.get("chapters", []))
                return f"Chủ đề {data.get('topic')} được trình bày trong {ch_list}."
            if "chapter" in entities:
                ch = data
                if "sub_topic" in entities:
                    return f"{ch.get('chapter_id')} ({ch.get('title')}) có nội dung liên quan đến {entities['sub_topic']}: {ch.get('summary')}."
                return f"{ch.get('chapter_id')} ({ch.get('title')}): {ch.get('summary')}."

        # 4. GET_LO
        elif intent == "GET_LO":
            desc = data.get("description", "")
            ch = data.get("chapter", "")
            ch_str = f" thuộc {ch}" if ch else ""
            return f"Chuẩn đầu ra {data.get('lo')}{ch_str}: {desc}."

        # 5. GET_ASSIGNMENT
        elif intent == "GET_ASSIGNMENT":
            if "part" in entities:
                reqs = ", ".join(data.get("requirements", []))
                return f"{data.get('id')} - {data.get('title')}: {reqs}."
            return f"Bài tập lớn ({data.get('title')}): {data.get('goal', '')} Làm việc theo nhóm {data.get('team_size', '3-4 sinh viên')}."

        # 6. GET_DEADLINE
        elif intent == "GET_DEADLINE":
            return f"Thời hạn hoàn thành bài tập lớn là: {data.get('deadline')}. Mốc checkpoint 1: {data.get('checkpoint1')}, checkpoint 2: {data.get('checkpoint2')}."

        # 7. GET_RULE
        elif intent == "GET_RULE":
            return f"Quy định môn học: {data}"

        # 8. GET_RESOURCE
        elif intent == "GET_RESOURCE":
            if isinstance(data, list) and data:
                books = [f"'{b.get('title')}' ({b.get('author') or b.get('id')})" for b in data]
                return f"Tài liệu tham khảo phù hợp: {'; '.join(books)}."
            return f"Tài liệu tham khảo: {data}"

        return self.FALLBACK_MESSAGE
