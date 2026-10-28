"""
Main Pipeline: Điều phối toàn bộ hệ thống Course Assistant (CO3085)
Phụ trách: Thành viên 4 (Lead Integrator)
Chạy toàn bộ: Phần I -> Phần II -> Phần III -> Phần IV
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.generator import SentenceGenerator
from src.parser import CourseParser
from src.semantic import SemanticInterpreter
from src.intent_entity import IntentEntityDetector
from src.knowledge_base import KnowledgeBase
from src.query_engine import QueryEngine
from src.nlg import AnswerGenerator
from src.dialogue import DialogueManager
from src.evaluator import SystemEvaluator

def main():
    print("==================================================================")
    print("COURSE ASSISTANT NLP SYSTEM - CO3085 (CLASSICAL NLP)")
    print("==================================================================")

    data_dir = "data"
    input_file = os.path.join("input", "sentences.txt")
    output_dir = "output"
    grammar_file = os.path.join("models", "grammar.cfg")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("input", exist_ok=True)

    # ------------------------------------------------------------------
    # PHẦN I: VIẾT VĂN PHẠM VÀ PARSER
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN I] VĂN PHẠM VÀ PARSER...")
    # 3.1: Xuất grammar.txt (Thành viên 1)
    out_grammar = os.path.join(output_dir, "grammar.txt")
    if os.path.exists(grammar_file):
        shutil.copyfile(grammar_file, out_grammar)

    # 3.2: Sinh câu samples.txt (Thành viên 2)
    out_samples = os.path.join(output_dir, "samples.txt")
    gen = SentenceGenerator(grammar_file)
    gen.save_samples(out_samples, max_samples=10000)

    # 3.3: Parser parse-results.txt (Thành viên 3)
    out_parse = os.path.join(output_dir, "parse-results.txt")
    parser = CourseParser(grammar_file)
    parser.process_file(input_file, out_parse)

    # ------------------------------------------------------------------
    # PHẦN II: DIỄN GIẢI NGỮ NGHĨA VÀ HỎI ĐÁP
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN II] DIỄN GIẢI NGỮ NGHĨA VÀ HỎI ĐÁP...")
    # 4.1.1: Semantic Representation -> semantic.txt (Thành viên 2)
    out_semantic = os.path.join(output_dir, "semantic.txt")
    interpreter = SemanticInterpreter()
    interpreter.process_file(input_file, out_semantic)

    # 4.1.2: Intent & Entity -> intent-entity.txt (Thành viên 2)
    out_intent_entity = os.path.join(output_dir, "intent-entity.txt")
    detector = IntentEntityDetector()
    detector.process_file(input_file, out_intent_entity)

    # 4.1.3: Knowledge Base & Query -> query.txt (Thành viên 3)
    kb = KnowledgeBase(data_dir)
    kb.load_data()
    query_engine = QueryEngine(kb)
    out_query = os.path.join(output_dir, "query.txt")
    # TODO: Thực thi ghi query.txt

    # 4.1.4: Answer Generation & Fallback -> answer.txt (Thành viên 3)
    nlg = AnswerGenerator(query_engine)
    out_answer = os.path.join(output_dir, "answer.txt")
    # TODO: Thực thi ghi answer.txt

    # ------------------------------------------------------------------
    # PHẦN III: XỬ LÝ NGỮ CẢNH HỘI THOẠI CỤC BỘ (Thành viên 4)
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN III] NGỮ CẢNH HỘI THOẠI CỤC BỘ...")
    dlg_manager = DialogueManager(detector, query_engine, nlg)
    dialogues_file = os.path.join(data_dir, "dialogues.txt")
    out_dialogue = os.path.join(output_dir, "dialogue.txt")
    dlg_manager.process_dialogues(dialogues_file, out_dialogue)

    # ------------------------------------------------------------------
    # PHẦN IV: ĐÁNH GIÁ HỆ THỐNG (Thành viên 4)
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN IV] ĐÁNH GIÁ HỆ THỐNG...")
    evaluator = SystemEvaluator(detector, parser, query_engine, nlg)
    sample_queries_file = os.path.join(data_dir, "sample_queries.txt")
    out_evaluation = os.path.join(output_dir, "evaluation.txt")
    evaluator.evaluate(sample_queries_file, out_evaluation)

    print("\n==================================================================")
    print("Pipeline hoàn tất!")
    print("==================================================================")

if __name__ == "__main__":
    main()
