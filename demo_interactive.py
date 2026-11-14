"""
Chế độ chạy thử trực quan (Interactive CLI & Step-by-Step Demo) cho Course Assistant (CO3085).
Hỗ trợ 2 chế độ:
  1. Chạy tự động 5 kịch bản mẫu phục vụ kiểm thử nhanh / quay Video Demo (Mục 7.6):
       ./venv/bin/python demo_interactive.py --demo
  2. Chế độ nhập câu hỏi trực tiếp từ bàn phím (có nhớ ngữ cảnh lượt trước):
       ./venv/bin/python demo_interactive.py
"""
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.parser import CourseParser
from src.semantic import SemanticInterpreter
from src.intent_entity import IntentEntityDetector
from src.knowledge_base import KnowledgeBase
from src.query_engine import QueryEngine
from src.nlg import AnswerGenerator
from src.dialogue import DialogueManager


class InteractiveAssistant:
    def __init__(self):
        grammar_path = os.path.join(PROJECT_ROOT, "models", "grammar.cfg")
        data_dir = os.path.join(PROJECT_ROOT, "data")
        self.parser = CourseParser(grammar_path)
        self.semantic = SemanticInterpreter(os.path.join(data_dir, "entities.txt"))
        self.detector = IntentEntityDetector(data_dir)
        self.kb = KnowledgeBase(data_dir).load_data()
        self.qe = QueryEngine(self.kb)
        self.nlg = AnswerGenerator(self.qe)
        self.dlg = DialogueManager(self.detector, self.qe, self.nlg)
        self.last_u1 = ""
        self.discourse_state = {}

    def ask(self, question: str):
        print("\n" + "=" * 78)
        print(f"[1] CÂU HỎI ĐẦU VÀO      : {question}")
        tokens = self.parser.tokenize(question)
        print(f"[2] TOKENIZATION         : {tokens}")
        tree_str = self.parser.parse_sentence(question)
        print(f"[3] CÂY CÚ PHÁP (CFG)    : {tree_str}")
        sem_str = self.semantic.interpret(question, tree_str)
        print(f"[4] BIỂU DIỄN NGỮ NGHĨA  : {sem_str}")
        intent, entities = self.detector.detect(tree_str)
        print(f"[5] INTENT & ENTITY      : Intent={intent} | Entities={entities}")

        if intent == "CONTEXT_DEPENDENT" and self.discourse_state:
            ctx_used, res_intent, res_ent, kb_query, answer = self.dlg.resolve_turn(
                self.last_u1, question, self.discourse_state
            )
            print(f"[6] NGỮ CẢNH HỘI THOẠI   : {ctx_used}")
            print(f"    -> Sau giải tham chiếu: Intent={res_intent} | Entities={res_ent}")
            if "chapter" in res_ent:
                self.discourse_state["chapter"] = res_ent["chapter"]
        else:
            kb_query = self.qe.build_query(intent, entities, question)
            answer = self.nlg.generate_answer(intent, entities, question)
            new_state = self.dlg._update_discourse_state(question, entities)
            if new_state:
                self.discourse_state.update(new_state)
                self.last_u1 = question

        print(f"[7] TRUY VẤN KB          : {kb_query}")
        print(f"[8] CÂU TRẢ LỜI HỆ THỐNG : {answer}")
        print("=" * 78)


def run_preset_demo():
    bot = InteractiveAssistant()
    print("******************************************************************************")
    print("CHẠY THỬ 6 KỊCH BẢN MẪU MINH HỌA TOÀN BỘ PIPELINE (PHỤC VỤ KIỂM THỬ & DEMO)")
    print("******************************************************************************")
    sample_questions = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Chương 4 nói về gì?",
        "Nó có liên quan đến parsing không?",
        "Có được dùng LLM/RAG không?",
        "Giảng viên phụ trách môn NLP là ai?",
        "Hôm nay ở TP.HCM có mưa không?",
    ]
    for q in sample_questions:
        bot.ask(q)


def run_interactive():
    bot = InteractiveAssistant()
    print("==============================================================================")
    print("CHẾ ĐỘ HỎI ĐÁP TRỰC TIẾP - COURSE ASSISTANT CO3085")
    print("Gõ câu hỏi tiếng Việt và nhấn Enter (gõ 'exit' hoặc 'quit' để thoát, 'reset' để xóa ngữ cảnh).")
    print("==============================================================================")
    while True:
        try:
            q = input("\nBạn hỏi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKết thúc phiên làm việc.")
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            print("Kết thúc phiên làm việc.")
            break
        if q.lower() == "reset":
            bot.discourse_state.clear()
            bot.last_u1 = ""
            print("-> Đã xóa bộ nhớ ngữ cảnh hội thoại.")
            continue
        bot.ask(q)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_preset_demo()
    elif len(sys.argv) > 1:
        bot = InteractiveAssistant()
        for arg_q in sys.argv[1:]:
            bot.ask(arg_q)
    else:
        run_interactive()
