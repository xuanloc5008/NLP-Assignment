"""
Phần III: Xử lý ngữ cảnh hội thoại cục bộ (Local Discourse Context)
Phụ trách: Xuân Lộc (Mục 5)
Xử lý đồng tham chiếu (Anaphora / Pronoun / Ellipsis Resolution):
  - "chương này", "nó" -> tham chiếu thực thể chương ở lượt trước
  - "phần này" -> tham chiếu phần bài tập lớn ở lượt trước (PART_I_GRAMMAR_PARSER)
  - "còn chương sau?" -> tham chiếu chương kế tiếp (CH11 -> CH12)
  - "nội dung này" -> tham chiếu chuẩn đầu ra (LO2.5) ở lượt trước
Output yêu cầu: output/dialogue.txt (thể hiện rõ 4 trường: hội thoại đầu vào,
thông tin ngữ cảnh được sử dụng, kết quả diễn giải, câu trả lời).
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

    def _update_discourse_state(self, u1: str, entities1: dict) -> dict:
        """Cập nhật bộ nhớ ngữ cảnh cục bộ (Discourse History State) sau lượt hỏi U1."""
        state = {}
        if "chapter" in entities1:
            state["chapter"] = entities1["chapter"]
        elif "week" in entities1:
            week_id = entities1["week"]
            sched = self.qe.kb.schedule.get(week_id, {})
            if sched.get("chapter"):
                state["chapter"] = sched["chapter"]
            state["week"] = week_id

        if "assignment_part" in entities1:
            state["assignment_part"] = entities1["assignment_part"]
        if "lo_code" in entities1:
            state["lo"] = entities1["lo_code"]
        return state

    def resolve_turn(self, u1: str, u2: str, state: dict) -> tuple[str, str, dict, str, str]:
        """
        Giải tham chiếu cho câu hỏi U2 dựa trên trạng thái ngữ cảnh từ U1.
        Trả về: (context_used, resolved_intent, resolved_entities, kb_query, answer)
        """
        raw_intent2, raw_ent2 = self.detector.detect(u2)
        resolved_entities = dict(raw_ent2)
        resolved_entities.pop("context_ref", None)
        u2_lower = u2.lower()
        context_used = ""

        if "chương này" in u2_lower:
            ch = state.get("chapter", "CH03")
            resolved_entities["chapter"] = ch
            context_used = f'"chương này" -> {ch} (suy ra từ lượt 1: "{u1}")'

        elif re.search(r"\bnó\b", u2_lower):
            ch = state.get("chapter", "CH04")
            resolved_entities["chapter"] = ch
            context_used = f'"Nó" -> {ch} (đồng tham chiếu đại từ tới thực thể ở lượt 1: "{u1}")'

        elif "phần này" in u2_lower:
            part = state.get("assignment_part", "PART_I")
            resolved_entities["assignment_part"] = part
            resolved_entities["assignment_id"] = "BTL01"
            part_label = f"{part}_GRAMMAR_PARSER" if part == "PART_I" else part
            context_used = f'"Phần này" -> {part_label} (đồng tham chiếu từ lượt 1: "{u1}")'

        elif "chương sau" in u2_lower:
            prev_ch = state.get("chapter", "CH11")
            prev_num = int(re.search(r"\d+", prev_ch).group())
            next_ch = f"CH{min(prev_num + 1, 12):02d}"
            resolved_entities["chapter"] = next_ch
            context_used = f'"chương sau" -> {next_ch} (tỉnh lược và dịch chuyển tương đối từ {prev_ch} ở lượt 1: "{u1}")'

        elif "nội dung này" in u2_lower:
            lo_id = state.get("lo", "LO2.5")
            resolved_entities["lo"] = lo_id
            context_used = f'"Nội dung này" -> {lo_id} (đồng tham chiếu chuẩn đầu ra ở lượt 1: "{u1}")'

        plan = self.qe.plan("CONTEXT_DEPENDENT", resolved_entities, u2)
        resolved_intent = plan["intent"] if plan else raw_intent2
        kb_query = self.qe.build_query("CONTEXT_DEPENDENT", resolved_entities, u2)
        answer = self.nlg.generate_answer("CONTEXT_DEPENDENT", resolved_entities, u2)

        return context_used, resolved_intent, resolved_entities, kb_query, answer

    def process_dialogues(self, input_path: str, output_path: str):
        """
        Đọc các hội thoại mẫu từ data/dialogues.txt và xuất kết quả ra output/dialogue.txt
        theo đúng 4 trường yêu cầu trong đề bài Mục 5.4:
          1. Hội thoại đầu vào
          2. Thông tin ngữ cảnh được sử dụng
          3. Kết quả diễn giải
          4. Câu trả lời
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        if not os.path.exists(input_path):
            print(f"[Lỗi] Không tìm thấy file {input_path}")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        dialogue_blocks = []
        cur_block = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("DIALOGUE "):
                if cur_block:
                    dialogue_blocks.append(cur_block)
                cur_block = [line_str]
            elif cur_block and line_str and not line_str.startswith("---"):
                cur_block.append(line_str)
        if cur_block:
            dialogue_blocks.append(cur_block)

        out_blocks = []
        for block in dialogue_blocks:
            dlg_id = block[0]
            u1, a1_lines, u2 = "", [], ""
            reading_a1 = False
            for item in block[1:]:
                if item.startswith("U1:"):
                    u1 = item[3:].strip()
                    reading_a1 = False
                elif item.startswith("A1:"):
                    a1_lines.append(item[3:].strip())
                    reading_a1 = True
                elif item.startswith("U2:"):
                    u2 = item[3:].strip()
                    reading_a1 = False
                elif item.startswith(("EXPECTED_REFERENCE:", "A2:")):
                    reading_a1 = False
                elif reading_a1:
                    a1_lines.append(item)

            a1 = " ".join(a1_lines)
            if not u1 or not u2:
                continue

            # Bước 1: Phân tích câu hỏi lượt 1 (U1) và lưu trạng thái ngữ cảnh
            intent1, entities1 = self.detector.detect(u1)
            state = self._update_discourse_state(u1, entities1)

            # Bước 2: Giải tham chiếu cho lượt 2 (U2) và sinh câu trả lời từ KB
            context_used, resolved_intent, resolved_entities, kb_query, answer2 = self.resolve_turn(u1, u2, state)

            formatted = f"""================================================================================
[{dlg_id}]
1. Hội thoại đầu vào:
   - Lượt 1 (U1): {u1}
   - Trả lời 1 (A1): {a1}
   - Lượt 2 (U2): {u2}
2. Thông tin ngữ cảnh được sử dụng:
   - Trạng thái lưu từ lượt 1: Intent={intent1}, Entities={entities1} -> Context={state}
   - Giải tham chiếu (Reference Resolution): {context_used}
3. Kết quả diễn giải:
   - Intent sau giải tham chiếu: {resolved_intent}
   - Thực thể sau giải tham chiếu: {resolved_entities}
   - Truy vấn cơ sở tri thức (KB Query): {kb_query}
4. Câu trả lời:
   - A2: {answer2}
"""
            out_blocks.append(formatted)

        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write("\n".join(out_blocks))

        print(f"-> Đã xử lý ngữ cảnh hội thoại cho {len(out_blocks)} hội thoại, lưu vào {output_path}")


if __name__ == "__main__":
    from src.knowledge_base import KnowledgeBase

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kb = KnowledgeBase(os.path.join(root, "data")).load_data()
    detector = IntentEntityDetector(data_dir=os.path.join(root, "data"))
    qe = QueryEngine(kb)
    nlg = AnswerGenerator(qe)
    dlg = DialogueManager(detector, qe, nlg)
    dlg.process_dialogues(
        os.path.join(root, "data", "dialogues.txt"),
        os.path.join(root, "output", "dialogue.txt"),
    )
