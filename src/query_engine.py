"""
Phần II.3: Xây dựng truy vấn tới Knowledge Base
Output: output/query.txt
"""
import os
from src.knowledge_base import KnowledgeBase

class QueryEngine:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def build_query(self, intent: str, entities: dict) -> str:
        """
        Chuyển (intent, entities) sang câu truy vấn có cấu trúc tương ứng.
        """
        if intent == "GET_COURSE_INFO":
            if entities.get("metric") == "CREDITS":
                return "SELECT credits, ects FROM course_info WHERE course_id='CO3085'"
            if entities.get("metric") == "PARTS":
                return "SELECT parts FROM course_info WHERE course_id='CO3085'"
            if "exam" in entities:
                return f"SELECT duration_minutes FROM exam_schedule WHERE exam='{entities['exam']}'"
            return "SELECT * FROM course_info WHERE course_id='CO3085'"

        elif intent == "GET_SCHEDULE":
            if "week" in entities:
                return f"SELECT chapter, topics FROM schedule WHERE week='{entities['week']}'"
            if "chapter" in entities:
                return f"SELECT week FROM schedule WHERE chapter='{entities['chapter']}'"
            return "SELECT * FROM schedule"

        elif intent == "GET_TOPIC":
            if "topic" in entities:
                return f"SELECT chapter_id, title FROM topics WHERE topic='{entities['topic']}'"
            if "chapter" in entities:
                sub = f" AND subtopic='{entities['sub_topic']}'" if "sub_topic" in entities else ""
                return f"SELECT title, summary, subtopics FROM topics WHERE chapter_id='{entities['chapter']}'{sub}"
            return "SELECT * FROM topics"

        elif intent == "GET_LO":
            return f"SELECT description, chapter FROM learning_outcomes WHERE lo_id='{entities.get('lo', '')}'"

        elif intent == "GET_ASSIGNMENT":
            if "part" in entities:
                return f"SELECT requirements, outputs FROM assignments WHERE assignment_id='BTL01' AND part='{entities['part']}'"
            return "SELECT title, goal, requirements FROM assignments WHERE assignment_id='BTL01'"

        elif intent == "GET_DEADLINE":
            return "SELECT deadline, milestone FROM assignments WHERE assignment_id='BTL01'"

        elif intent == "GET_RULE":
            return f"SELECT regulation FROM regulations WHERE topic='{entities.get('rule_topic', 'ALL')}'"

        elif intent == "GET_RESOURCE":
            return f"SELECT * FROM resources WHERE topic='{entities.get('resource_topic', 'GENERAL')}'"

        elif intent == "CONTEXT_DEPENDENT":
            return f"RESOLVE_CONTEXT({entities})"

        return "NO_QUERY(OUT_OF_SCOPE)"

    def execute_query(self, intent: str, entities: dict) -> any:
        """
        Thực thi câu truy vấn trên Knowledge Base và trả về dữ liệu kết quả.
        """
        if intent == "GET_COURSE_INFO":
            if entities.get("metric") == "CREDITS":
                return {
                    "credits": self.kb.course_info.get("credits", 3),
                    "ects": self.kb.course_info.get("ects", 6),
                    "course_name": self.kb.course_info.get("course_name", "Xử lý Ngôn ngữ Tự nhiên"),
                    "course_id": self.kb.course_info.get("course_id", "CO3085")
                }
            if entities.get("metric") == "PARTS":
                return self.kb.course_info.get("parts", [])
            if entities.get("exam") == "MIDTERM":
                return {"exam": "Midterm", "minutes": self.kb.course_info.get("midterm_minutes", 60)}
            if entities.get("exam") == "FINAL":
                return {"exam": "Final", "minutes": self.kb.course_info.get("final_minutes", 90)}
            return self.kb.course_info

        elif intent == "GET_SCHEDULE":
            w = entities.get("week")
            if w and w in self.kb.schedule:
                return self.kb.schedule[w]
            ch = entities.get("chapter")
            if ch:
                weeks = self.kb.weeks_of_chapter(ch)
                return {"chapter": ch, "weeks": weeks, "title": self.kb.topics.get(ch, {}).get("title", "")}
            return self.kb.schedule

        elif intent == "GET_TOPIC":
            ch = entities.get("chapter")
            if ch and ch in self.kb.topics:
                ch_data = self.kb.topics[ch]
                if "sub_topic" in entities:
                    return {"chapter": ch, "title": ch_data["title"], "sub_topic": entities["sub_topic"], "summary": ch_data["summary"]}
                return ch_data

            tp = entities.get("topic")
            if tp:
                matched = self.kb.find_chapters_for_terms([tp, tp.replace("_", " ")])
                if matched:
                    chapters = [cid for cid, score in matched]
                    return {"topic": tp, "chapters": chapters}
            return None

        elif intent == "GET_LO":
            lo_id = entities.get("lo", "")
            desc = self.kb.learning_outcomes.get(lo_id, "")
            ch = self.kb.lo_to_chapter.get(lo_id, "")
            if desc or ch:
                return {"lo": lo_id, "description": desc, "chapter": ch}
            return None

        elif intent == "GET_ASSIGNMENT":
            btl = self.kb.assignments.get("BTL01", {})
            part = entities.get("part")
            if part and part in btl.get("parts", {}):
                return btl["parts"][part]
            return btl

        elif intent == "GET_DEADLINE":
            return {
                "deadline": "Cuối tuần 12 của học kỳ (trước các tuần thuyết trình 13-14)",
                "checkpoint1": "Tuần 8 (BTL checkpoint 1: Grammar and Parser)",
                "checkpoint2": "Tuần 12 (BTL checkpoint 2: Semantic Interpretation and QA)"
            }

        elif intent == "GET_RULE":
            topic = entities.get("rule_topic", "AI_USAGE")
            if topic == "LLM_RAG":
                return self.kb.regulations.get("LLM_RAG", "LLM/RAG nếu được sử dụng chỉ nên đóng vai trò mở rộng, không thay thế các yêu cầu NLP cốt lõi.")
            return self.kb.regulations.get("AI_USAGE", "Sinh viên phải khai báo việc sử dụng AI trong báo cáo và không dùng AI để thay thế thành phần NLP cốt lõi.")

        elif intent == "GET_RESOURCE":
            topic = entities.get("resource_topic", "GENERAL")
            if topic == "STATISTICAL_NLP":
                return [r for r in self.kb.resources if "statistical" in r["usage"].lower() or "statistical" in r["title"].lower()]
            if topic == "PYTHON_NLP":
                return [r for r in self.kb.resources if "python" in r["usage"].lower() or "python" in r["title"].lower()]
            return self.kb.resources[:3]

        return None
