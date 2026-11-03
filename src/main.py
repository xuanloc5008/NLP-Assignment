"""
Main Pipeline: Điều phối toàn bộ hệ thống Course Assistant (CO3085)
Hướng tiếp cận: Classical / Statistical NLP
Chạy toàn bộ:
  - Phần I: Văn phạm, Sinh câu, Phân tích cú pháp (Mục 3.1, 3.2, 3.3)
  - Phần II: Diễn giải ngữ nghĩa, Intent/Entity, Truy vấn KB, Sinh câu trả lời & Fallback (Mục 4.1)
  - Phần III: Xử lý ngữ cảnh hội thoại cục bộ (Mục 5)
  - Phần IV: Đánh giá hệ thống trên tập dữ liệu kiểm thử (Mục 6)
Xuất đầy đủ 9 file output vào thư mục output/.
"""
import os
import shutil
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.generator import SentenceGenerator
from src.parser import CourseParser
from src.semantic import SemanticInterpreter
from src.intent_entity import IntentEntityDetector
from src.knowledge_base import KnowledgeBase
from src.query_engine import QueryEngine
from src.nlg import AnswerGenerator
from src.dialogue import DialogueManager
from src.evaluator import SystemEvaluator

def run_pipeline() -> bool:
    print("=" * 70)
    print("HỆ THỐNG TRỢ LÝ HỌC TẬP THÔNG MINH - COURSE ASSISTANT (CO3085)")
    print("Pipeline: Classical / Statistical NLP (Toàn diện Phần I -> IV)")
    print("=" * 70)

    data_dir = os.path.join(PROJECT_ROOT, "data")
    input_file = os.path.join(PROJECT_ROOT, "input", "sentences.txt")
    output_dir = os.path.join(PROJECT_ROOT, "output")
    grammar_file = os.path.join(PROJECT_ROOT, "models", "grammar.cfg")
    dialogues_file = os.path.join(data_dir, "dialogues.txt")
    sample_queries_file = os.path.join(data_dir, "sample_queries.txt")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "input"), exist_ok=True)

    # ------------------------------------------------------------------
    # PHẦN I: VIẾT VĂN PHẠM VÀ PARSER
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN I] VĂN PHẠM VÀ PARSER...")
    # 3.1: Xuất grammar.txt
    out_grammar = os.path.join(output_dir, "grammar.txt")
    if os.path.exists(grammar_file):
        shutil.copyfile(grammar_file, out_grammar)
        print(f"  [3.1] Đã tạo: {out_grammar}")

    # 3.2: Sinh câu samples.txt
    out_samples = os.path.join(output_dir, "samples.txt")
    gen = SentenceGenerator(grammar_file)
    gen.save_samples(out_samples, max_samples=10000)

    # 3.3: Parser parse-results.txt
    out_parse = os.path.join(output_dir, "parse-results.txt")
    parser = CourseParser(grammar_file)
    parser.process_file(input_file, out_parse)

    # ------------------------------------------------------------------
    # PHẦN II: DIỄN GIẢI NGỮ NGHĨA VÀ HỎI ĐÁP
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN II] DIỄN GIẢI NGỮ NGHĨA VÀ HỎI ĐÁP...")
    # 4.1.1: Semantic Representation -> semantic.txt
    out_semantic = os.path.join(output_dir, "semantic.txt")
    interpreter = SemanticInterpreter()
    interpreter.process_file(input_file, out_semantic)
    print(f"  [4.1.1] Đã tạo: {out_semantic}")

    # 4.1.2: Intent & Entity -> intent-entity.txt
    out_intent_entity = os.path.join(output_dir, "intent-entity.txt")
    detector = IntentEntityDetector()
    detector.process_file(input_file, out_intent_entity)
    print(f"  [4.1.2] Đã tạo: {out_intent_entity}")

    # Khởi tạo Knowledge Base & Query Engine
    kb = KnowledgeBase(data_dir)
    query_engine = QueryEngine(kb)
    nlg = AnswerGenerator(query_engine)

    # 4.1.3: Knowledge Base Query -> query.txt
    out_query = os.path.join(output_dir, "query.txt")
    # 4.1.4 & 4.1.5: Answer Generation & Fallback -> answer.txt
    out_answer = os.path.join(output_dir, "answer.txt")

    with open(input_file, "r", encoding="utf-8") as fin, \
         open(out_query, "w", encoding="utf-8") as f_q, \
         open(out_answer, "w", encoding="utf-8") as f_a:
        for line in fin:
            line_str = line.strip()
            if not line_str:
                continue
            it, et = detector.detect(line_str)
            q_str = query_engine.build_query(it, et)
            ans_str = nlg.generate_answer(it, et)
            f_q.write(q_str + "\n")
            f_a.write(ans_str + "\n")

    print(f"  [4.1.3] Đã tạo: {out_query}")
    print(f"  [4.1.4] Đã tạo: {out_answer}")

    # ------------------------------------------------------------------
    # PHẦN III: XỬ LÝ NGỮ CẢNH HỘI THOẠI CỤC BỘ
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN III] NGỮ CẢNH HỘI THOẠI CỤC BỘ...")
    dlg_manager = DialogueManager(detector, query_engine, nlg)
    out_dialogue = os.path.join(output_dir, "dialogue.txt")
    dlg_manager.process_dialogues(dialogues_file, out_dialogue)

    # ------------------------------------------------------------------
    # PHẦN IV: ĐÁNH GIÁ HỆ THỐNG
    # ------------------------------------------------------------------
    print("\n>>> [PHẦN IV] ĐÁNH GIÁ HỆ THỐNG...")
    evaluator = SystemEvaluator(detector, parser, query_engine, nlg)
    out_evaluation = os.path.join(output_dir, "evaluation.txt")
    evaluator.evaluate(sample_queries_file, out_evaluation)

    # ------------------------------------------------------------------
    # KIỂM TRA ĐẦU RA 9 FILE BẮT BUỘC
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("KIỂM TRA CÁC FILE OUTPUT:")
    expected_files = [
        "grammar.txt", "samples.txt", "parse-results.txt",
        "semantic.txt", "intent-entity.txt", "query.txt", "answer.txt",
        "dialogue.txt", "evaluation.txt"
    ]
    all_ok = True
    for fname in expected_files:
        fpath = os.path.join(output_dir, fname)
        exists = os.path.exists(fpath) and os.path.getsize(fpath) > 0
        status = "[OK]  " if exists else "[FAIL]"
        print(f"  {status} {fname}")
        if not exists:
            all_ok = False

    print("=" * 70)
    if all_ok:
        print("HOÀN TẤT THÀNH CÔNG 100% CÁC PHẦN (I, II, III, IV) THEO YÊU CẦU ĐỀ BÀI!")
    else:
        print("Vẫn còn file output chưa được sinh đầy đủ. Vui lòng kiểm tra lại log.")
    print("=" * 70)
    return all_ok

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
