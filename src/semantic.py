"""
Phần II.1: Xây dựng biểu diễn ngữ nghĩa (Semantic Representation)
Ánh xạ từ câu tự nhiên hoặc cây cú pháp sang biểu diễn logic / vị từ (Predicate / Logical Form).
Output: output/semantic.txt
"""
import os
from src.intent_entity import IntentEntityDetector

class SemanticInterpreter:
    def __init__(self):
        self.detector = IntentEntityDetector()

    def interpret(self, sentence: str, parse_tree_str: str = "()") -> str:
        """
        Nhận diện câu và sinh biểu diễn ngữ nghĩa logic:
        Ví dụ:
          "Môn NLP có bao nhiêu tín chỉ?" -> GET_CREDIT(course=CO3085)
          "Tuần 3 học gì?"               -> GET_SCHEDULE(week=WEEK_03)
          "Deadline bài tập lớn là khi nào?" -> GET_DEADLINE(assignment=PROJECT)
        """
        intent, entities = self.detector.detect(sentence, parse_tree_str)

        if intent == "GET_COURSE_INFO":
            if entities.get("metric") == "CREDITS":
                return f"GET_CREDIT(course={entities.get('course', 'CO3085')})"
            if entities.get("metric") == "PARTS":
                return f"GET_PARTS(course={entities.get('course', 'CO3085')})"
            if "exam" in entities:
                return f"GET_EXAM_DURATION(exam={entities['exam']})"
            return f"GET_COURSE_INFO(course={entities.get('course', 'CO3085')})"

        elif intent == "GET_SCHEDULE":
            if "week" in entities:
                return f"GET_SCHEDULE(week={entities['week']})"
            if "chapter" in entities:
                return f"GET_WEEK(chapter={entities['chapter']})"
            return "GET_SCHEDULE(target=ALL)"

        elif intent == "GET_TOPIC":
            if "topic" in entities:
                return f"GET_CHAPTER(topic={entities['topic']})"
            if "chapter" in entities:
                sub = f", subtopic={entities['sub_topic']}" if "sub_topic" in entities else ""
                return f"GET_TOPIC(chapter={entities['chapter']}{sub})"
            return "GET_TOPIC(target=GENERAL)"

        elif intent == "GET_LO":
            return f"GET_LO_INFO(lo={entities.get('lo', 'UNKNOWN')})"

        elif intent == "GET_ASSIGNMENT":
            if "part" in entities:
                return f"GET_ASSIGNMENT(part={entities['part']})"
            return f"GET_ASSIGNMENT(assignment={entities.get('assignment', 'BTL01')})"

        elif intent == "GET_DEADLINE":
            return f"GET_DEADLINE(assignment={entities.get('assignment', 'PROJECT')})"

        elif intent == "GET_RULE":
            return f"GET_RULE(topic={entities.get('rule_topic', 'AI_USAGE')})"

        elif intent == "GET_RESOURCE":
            return f"GET_RESOURCE(topic={entities.get('resource_topic', 'GENERAL')})"

        elif intent == "CONTEXT_DEPENDENT":
            slots = []
            for k, v in entities.items():
                if k != "primary":
                    slots.append(f"{k}={v}")
            slot_str = ", ".join(slots) if slots else "target=PREVIOUS_CONTEXT"
            return f"CONTEXT_REF({slot_str})"

        return "UNKNOWN_SEMANTIC(scope=OUT_OF_SCOPE)"

    def process_file(self, input_path: str, output_path: str):
        """Đọc input/sentences.txt và ghi kết quả biểu diễn ngữ nghĩa vào output_path"""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(input_path, "r", encoding="utf-8") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                sem = self.interpret(line)
                fout.write(sem + "\n")

if __name__ == "__main__":
    interp = SemanticInterpreter()
    demo = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học gì?",
        "Chương 4 học vào tuần nào?",
        "Chương nào nói về CFG?",
        "Deadline của bài tập lớn là khi nào?",
        "Hôm nay ở TP.HCM có mưa không?"
    ]
    for s in demo:
        print(f"{s} -> {interp.interpret(s)}")
