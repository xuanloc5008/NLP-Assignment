"""
Script chạy kiểm thử riêng Phần I (Grammar, Generation, Parser)
Phụ trách: Thành viên 4 (Lead Integrator) tổng hợp từ Thành viên 1, 2, 3
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.generator import SentenceGenerator
from src.parser import CourseParser

def run_part1():
    print("=" * 60)
    print("CHẠY PHẦN I: VIẾT VĂN PHẠM VÀ PARSER")
    print("=" * 60)

    grammar_cfg = os.path.join("models", "grammar.cfg")
    out_grammar = os.path.join("output", "grammar.txt")
    out_samples = os.path.join("output", "samples.txt")
    in_sentences = os.path.join("input", "sentences.txt")
    out_parse = os.path.join("output", "parse-results.txt")

    os.makedirs("output", exist_ok=True)
    os.makedirs("input", exist_ok=True)

    # 1. Mục 3.1: Xuất văn phạm (Thành viên 1)
    print("[1/3] Xuất văn phạm (Mục 3.1)...")
    if os.path.exists(grammar_cfg):
        shutil.copyfile(grammar_cfg, out_grammar)
        print(f"-> Đã tạo {out_grammar}")

    # 2. Mục 3.2: Sinh câu (Thành viên 2)
    print("[2/3] Sinh câu hợp lệ (Mục 3.2)...")
    gen = SentenceGenerator(grammar_cfg)
    gen.save_samples(out_samples, max_samples=10000)

    # 3. Mục 3.3: Parser (Thành viên 3)
    print("[3/3] Phân tích cú pháp (Mục 3.3)...")
    parser = CourseParser(grammar_cfg)
    parser.process_file(in_sentences, out_parse)

    print("=" * 60)
    print("Hoàn thành Phần I!")
    print("=" * 60)

if __name__ == "__main__":
    run_part1()
