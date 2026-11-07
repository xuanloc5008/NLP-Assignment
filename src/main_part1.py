"""
Chạy tổng hợp Phần I: Viết văn phạm và Parser (Mục 3.1 + 3.2 + 3.3)
Phụ trách: Xuân Lộc (Lead Integrator)

    python3 -m src.main_part1

Sinh đủ 3 file trong output/:
    grammar.txt        (3.1 - Nam)   : bản sao tập luật models/grammar.cfg
    samples.txt        (3.2 - Nhân)  : tối đa 10.000 câu hợp lệ sinh từ văn phạm
    parse-results.txt  (3.3 - Đức Anh): cây cú pháp / '()' cho từng câu của input/sentences.txt
Cuối cùng tự kiểm tra định dạng các file này.
"""
import os
import shutil
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.generator import SentenceGenerator
from src.parser import CourseParser

GRAMMAR_CFG = os.path.join(PROJECT_ROOT, "models", "grammar.cfg")
IN_SENTENCES = os.path.join(PROJECT_ROOT, "input", "sentences.txt")
OUT_GRAMMAR = os.path.join(PROJECT_ROOT, "output", "grammar.txt")
OUT_SAMPLES = os.path.join(PROJECT_ROOT, "output", "samples.txt")
OUT_PARSE = os.path.join(PROJECT_ROOT, "output", "parse-results.txt")


def _read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f if l.strip()]


def validate() -> bool:
    """Kiểm tra định dạng 3 file output theo yêu cầu đề bài."""
    ok = True

    def check(cond: bool, msg: str):
        nonlocal ok
        print(("  [OK]   " if cond else "  [FAIL] ") + msg)
        ok &= cond

    print("\n--- Kiểm tra định dạng output ---")
    check(os.path.exists(OUT_GRAMMAR) and os.path.getsize(OUT_GRAMMAR) > 0, "grammar.txt tồn tại và không rỗng")

    samples = _read_lines(OUT_SAMPLES) if os.path.exists(OUT_SAMPLES) else []
    check(0 < len(samples) <= 10000, f"samples.txt có {len(samples)} câu (1..10000)")
    check(len(samples) == len(set(samples)), "samples.txt không có câu trùng")

    sentences = _read_lines(IN_SENTENCES)
    results = _read_lines(OUT_PARSE) if os.path.exists(OUT_PARSE) else []
    check(len(results) == len(sentences),
          f"parse-results.txt có {len(results)} dòng = {len(sentences)} câu input")
    check(all(r == "()" or (r.startswith("(S") and r.endswith(")")) for r in results),
          "mỗi dòng parse-results là cây '(S ...)' hoặc '()'")
    return ok


def run_part1() -> bool:
    print("=" * 60)
    print("CHẠY PHẦN I: VIẾT VĂN PHẠM VÀ PARSER")
    print("=" * 60)
    os.makedirs(os.path.join(PROJECT_ROOT, "output"), exist_ok=True)

    print("\n[1/3] Mục 3.1 - xuất văn phạm")
    shutil.copyfile(GRAMMAR_CFG, OUT_GRAMMAR)
    print(f"  -> {OUT_GRAMMAR}")

    print("\n[2/3] Mục 3.2 - sinh câu")
    SentenceGenerator(GRAMMAR_CFG).save_samples(OUT_SAMPLES, max_samples=10000)

    print("\n[3/3] Mục 3.3 - phân tích cú pháp")
    CourseParser(GRAMMAR_CFG).process_file(IN_SENTENCES, OUT_PARSE)

    ok = validate()
    print("\n" + "=" * 60)
    print("HOÀN THÀNH PHẦN I" if ok else "PHẦN I CÒN LỖI - xem các dòng [FAIL] ở trên")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_part1() else 1)
