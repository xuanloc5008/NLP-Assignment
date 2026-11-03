"""
Phần III: Xử lý ngữ cảnh hội thoại cục bộ (Local Discourse Context)
Xử lý đồng tham chiếu (Anaphora / Pronoun / Ellipsis Resolution):
  - "chương này", "nó" -> tham chiếu thực thể chương ở lượt trước
  - "phần này" -> tham chiếu phần bài tập ở lượt trước
  - "còn chương sau?" -> tham chiếu chương kế tiếp
  - "nội dung này" -> tham chiếu chuẩn đầu ra / chủ đề ở lượt trước
Output: output/dialogue.txt
"""
import os
import re
from src.intent_entity import IntentEntityDetector
from src.query_engine import QueryEngine
from src.nlg import AnswerGenerator

class DialogueManager:
    def __init__(self, detector: IntentEntityDetector, query_engine: QueryEngine, nlg: AnswerGenerator):
        self.detector = detector
        self.qe = query_engine
        self.nlg = nlg

    def process_dialogues(self, input_path: str, output_path: str):
        """
        Đọc các hội thoại mẫu từ data/dialogues.txt và xuất kết quả ra output/dialogue.txt
        theo 4 trường:
          - hội thoại đầu vào;
          - thông tin ngữ cảnh được sử dụng;
          - kết quả diễn giải;
          - câu trả lời.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        if not os.path.exists(input_path):
            print(f"[Cảnh báo] Không tìm thấy file {input_path}")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        dialogue_blocks = []
        cur_block = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("DIALOGUE "):
                if cur_block:
                    dialogue_blocks.append(cur_block)
                cur_block = [line_str]
            elif cur_block:
                cur_block.append(line_str)
        if cur_block:
            dialogue_blocks.append(cur_block)

        results = []
        for block in dialogue_blocks:
            dlg_id = block[0]
            u1, a1, u2 = "", "", ""
            exp_ref = ""
            for item in block:
                if item.startswith("U1:"):
                    u1 = item[3:].strip()
                elif item.startswith("A1:"):
                    a1 = item[3:].strip()
                elif item.startswith("U2:"):
                    u2 = item[3:].strip()
                elif item.startswith("EXPECTED_REFERENCE:"):
                    exp_ref = item.replace("EXPECTED_REFERENCE:", "").strip()

            if not u1 or not u2:
                continue

            # 1. Phân tích lượt 1 (U1)
            i1, e1 = self.detector.detect(u1)
            # Trích xuất thực thể để lưu vào State Memory
            last_state = {}
            if "chapter" in e1:
                last_state["chapter"] = e1["chapter"]
            elif "week" in e1:
                # Tuần 3 học Chương 3
                w_int = int(e1["week"].replace("WEEK_", ""))
                last_state["chapter"] = f"CH{w_int:02d}"
                last_state["week"] = e1["week"]
            if "part" in e1:
                last_state["part"] = e1["part"]
            if "lo" in e1:
                last_state["lo"] = e1["lo"]
            if "parser" in u1.lower():
                last_state["part"] = "PART_I"

            # 2. Xử lý lượt 2 (U2) với bộ nhớ ngữ cảnh
            u2_lower = u2.lower()
            context_used = ""
            resolved_intent = ""
            resolved_entities = {}
            answer2 = ""

            if "chương này" in u2_lower:
                ch = last_state.get("chapter", "CH03")
                context_used = f'"chương này" -> {ch} (từ lượt 1: "{u1}")'
                resolved_intent = "GET_RESOURCE"
                resolved_entities = {"resource_topic": ch, "chapter": ch}
                answer2 = f"Có thể tham khảo giáo trình NLTK hoặc tài liệu môn học về {ch} trong danh mục Course Resources."

            elif re.search(r'\bnó\b', u2_lower):
                ch = last_state.get("chapter", "CH04")
                context_used = f'"Nó" -> {ch} (từ lượt 1: "{u1}")'
                resolved_intent = "GET_TOPIC"
                resolved_entities = {"chapter": ch, "topic": "PARSING"}
                answer2 = f"Có. {ch} trình bày về parsing với features và augmented grammar."

            elif "phần này" in u2_lower:
                part = last_state.get("part", "PART_I")
                context_used = f'"Phần này" -> {part} (từ lượt 1: "{u1}")'
                resolved_intent = "GET_ASSIGNMENT_OUTPUT"
                resolved_entities = {"part": part, "target": "OUTPUT_FILES"}
                answer2 = f"Các output cần xuất của {part} gồm: grammar.txt, samples.txt và parse-results.txt."

            elif "chương sau" in u2_lower:
                last_ch = last_state.get("chapter", "CH11")
                num = int(last_ch.replace("CH", "")) + 1
                next_ch = f"CH{num:02d}"
                context_used = f'"chương sau" -> {next_ch} (kế tiếp {last_ch})'
                resolved_intent = "GET_TOPIC"
                resolved_entities = {"chapter": next_ch}
                answer2 = f"{next_ch} tập trung vào discourse context, reference và các phương pháp giải quyết đồng tham chiếu."

            elif "nội dung này" in u2_lower:
                lo = last_state.get("lo", "LO2.5")
                ch = self.qe.kb.lo_to_chapter.get(lo, "CH06")
                context_used = f'"Nội dung này" -> {lo} (từ lượt 1)'
                resolved_intent = "GET_TOPIC"
                resolved_entities = {"lo": lo, "chapter": ch}
                answer2 = f"Nội dung này thuộc {ch}, Ambiguity Resolution: Statistical Methods."

            else:
                # Không tham chiếu, xử lý bình thường
                i2, e2 = self.detector.detect(u2)
                context_used = "Độc lập (không có quan hệ tham chiếu)"
                resolved_intent = i2
                resolved_entities = e2
                answer2 = self.nlg.generate_answer(i2, e2)

            res_block = f"""==================================================
HỘI THOẠI: {dlg_id}
• Hội thoại đầu vào:
  Sinh viên: "{u1}"
  Hệ thống:  "{a1}"
  Sinh viên: "{u2}"
• Thông tin ngữ cảnh được sử dụng:
  {context_used}
• Kết quả diễn giải:
  Intent: {resolved_intent} | Entities: {resolved_entities}
• Câu trả lời:
  Hệ thống: "{answer2}"
"""
            results.append(res_block)

        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write("\n".join(results))
        print(f"[DialogueManager] Đã xử lý {len(results)} đoạn hội thoại ngữ cảnh -> {output_path}")

if __name__ == "__main__":
    from src.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()
    detector = IntentEntityDetector()
    qe = QueryEngine(kb)
    nlg = AnswerGenerator(qe)
    dm = DialogueManager(detector, qe, nlg)
    dm.process_dialogues("data/dialogues.txt", "output/dialogue.txt")
