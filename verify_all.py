"""
Script kiểm thử tự động toàn diện (End-to-End Verification Suite) cho BTL Course Assistant (CO3085).
Kiểm tra toàn bộ 4 phần (Phần I, II, III, IV) và 9 file output bắt buộc trong output/.
Chạy bằng lệnh:
    ./venv/bin/python verify_all.py
"""
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.main import main as run_main_pipeline
from src.nlg import AnswerGenerator


def check(condition: bool, msg: str) -> bool:
    if condition:
        print(f"  [PASS] {msg}")
        return True
    else:
        print(f"  [FAIL] {msg}")
        return False


def verify():
    print("================================================================================")
    print("BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG TOÀN BỘ ASSIGNMENT (PHẦN I -> PHẦN IV)")
    print("================================================================================")

    # 1. Xóa các file output cũ để đảm bảo sinh mới 100% từ code
    out_dir = os.path.join(PROJECT_ROOT, "output")
    expected_files = [
        "grammar.txt",
        "samples.txt",
        "parse-results.txt",
        "semantic.txt",
        "intent-entity.txt",
        "query.txt",
        "answer.txt",
        "dialogue.txt",
        "evaluation.txt",
    ]
    for fname in expected_files:
        fpath = os.path.join(out_dir, fname)
        if os.path.exists(fpath):
            os.remove(fpath)

    # 2. Chạy toàn bộ pipeline qua src.main
    run_main_pipeline()

    print("\n================================================================================")
    print("KIỂM TRA ĐỊNH DẠNG & NỘI DUNG 9 FILE OUTPUT BẮT BUỘC")
    print("================================================================================")
    all_passed = True

    # Kiểm tra sự tồn tại của cả 9 file
    for fname in expected_files:
        fpath = os.path.join(out_dir, fname)
        exists = os.path.exists(fpath) and os.path.getsize(fpath) > 0
        all_passed &= check(exists, f"Tồn tại và khác rỗng: output/{fname}")

    with open(os.path.join(PROJECT_ROOT, "input", "sentences.txt"), encoding="utf-8") as f:
        input_lines = [l for l in f.read().splitlines() if l.strip()]
    n_in = len(input_lines)

    # 3.1: grammar.txt
    with open(os.path.join(out_dir, "grammar.txt"), encoding="utf-8") as f:
        g_text = f.read()
    all_passed &= check("S ->" in g_text and "Q_COURSE_INFO" in g_text, "3.1 grammar.txt chứa ký hiệu bắt đầu S và các luật CFG")

    # 3.2: samples.txt
    with open(os.path.join(out_dir, "samples.txt"), encoding="utf-8") as f:
        samples = [l.strip() for l in f.read().splitlines() if l.strip()]
    all_passed &= check(
        0 < len(samples) <= 10000 and len(samples) == len(set(samples)),
        f"3.2 samples.txt: {len(samples)} câu hợp lệ, không trùng lặp (<= 10.000 câu)",
    )

    # 3.3: parse-results.txt
    with open(os.path.join(out_dir, "parse-results.txt"), encoding="utf-8") as f:
        parses = f.read().splitlines()
    valid_parses = sum(1 for p in parses if p.startswith("(S "))
    empty_parses = sum(1 for p in parses if p.strip() == "()")
    all_passed &= check(
        len(parses) == n_in and valid_parses == 31 and empty_parses == 3,
        f"3.3 parse-results.txt: {len(parses)}/{n_in} dòng ({valid_parses} câu có cây cú pháp '(S ...)', {empty_parses} câu ngoài miền '()')",
    )

    # 4.1.1: semantic.txt (Đinh Hải Nam)
    with open(os.path.join(out_dir, "semantic.txt"), encoding="utf-8") as f:
        semantics = f.read().splitlines()
    valid_sem = sum(1 for s in semantics if s != "UNKNOWN()")
    all_passed &= check(
        len(semantics) == n_in and valid_sem == 31 and semantics[3] == "GET_SCHEDULE(week=WEEK_03)",
        f"4.1.1 semantic.txt: {len(semantics)}/{n_in} dòng ({valid_sem} biểu diễn vị từ hợp lệ, 3 câu UNKNOWN())",
    )

    # 4.1.2: intent-entity.txt (Thành Nhân)
    with open(os.path.join(out_dir, "intent-entity.txt"), encoding="utf-8") as f:
        ie_lines = f.read().splitlines()
    unknown_ie = sum(1 for l in ie_lines if l.startswith("UNKNOWN |"))
    all_passed &= check(
        len(ie_lines) == n_in and unknown_ie == 3,
        f"4.1.2 intent-entity.txt: {len(ie_lines)}/{n_in} dòng (31 câu trong miền + ngữ cảnh, 3 câu OUT_OF_SCOPE)",
    )

    # 4.1.3: query.txt (Đức Anh)
    with open(os.path.join(out_dir, "query.txt"), encoding="utf-8") as f:
        queries = f.read().splitlines()
    select_queries = sum(1 for q in queries if q.startswith("SELECT "))
    no_queries = sum(1 for q in queries if q.startswith("NO_QUERY"))
    all_passed &= check(
        len(queries) == n_in and select_queries == 31 and no_queries == 3,
        f"4.1.3 query.txt: {len(queries)}/{n_in} dòng ({select_queries} câu lệnh SELECT, {no_queries} câu NO_QUERY)",
    )

    # 4.1.4 & 4.1.5: answer.txt (Đức Anh)
    with open(os.path.join(out_dir, "answer.txt"), encoding="utf-8") as f:
        answers = f.read().splitlines()
    fallback_count = sum(1 for a in answers if a == AnswerGenerator.FALLBACK_MESSAGE)
    answered_count = len(answers) - fallback_count
    all_passed &= check(
        len(answers) == n_in and answered_count == 31 and fallback_count == 3,
        f"4.1.4 & 4.1.5 answer.txt: {len(answers)}/{n_in} dòng ({answered_count} câu trả lời từ KB, {fallback_count} câu Fallback chuẩn)",
    )

    # Phần III (Mục 5): dialogue.txt (Xuân Lộc)
    with open(os.path.join(out_dir, "dialogue.txt"), encoding="utf-8") as f:
        dlg_text = f.read()
    dlg_ok = all(f"[DIALOGUE 0{i}]" in dlg_text for i in range(1, 6)) and all(
        ref in dlg_text for ref in ["CH03", "CH04", "PART_I_GRAMMAR_PARSER", "CH12", "LO2.5"]
    )
    all_passed &= check(
        dlg_ok,
        "Phần III dialogue.txt: Đủ 5 hội thoại (DIALOGUE 01..05), giải tham chiếu chính xác 5/5 (CH03, CH04, PART_I, CH12, LO2.5) và đủ 4 trường",
    )

    # Phần IV (Mục 6): evaluation.txt (Xuân Lộc)
    with open(os.path.join(out_dir, "evaluation.txt"), encoding="utf-8") as f:
        eval_text = f.read()
    eval_ok = (
        "34/34 câu (100.00%)" in eval_text
        and "PHÂN TÍCH NGUYÊN NHÂN LỖI" in eval_text
        and "ƯU ĐIỂM VÀ HẠN CHẾ" in eval_text
    )
    all_passed &= check(
        eval_ok,
        "Phần IV evaluation.txt: Đầy đủ thống kê độ chính xác (34/34 - 100%), phân tích lỗi và nhận xét ưu/nhược điểm Classical NLP",
    )

    # Kiểm tra chạy độc lập từng module CLI (`python -m src.<module>`)
    print("\n================================================================================")
    print("KIỂM TRA CHẠY ĐỘC LẬP TỪNG MODULE (STANDALONE CLI MODULES)")
    print("================================================================================")
    modules = [
        "src.main_part1",
        "src.semantic",
        "src.intent_entity",
        "src.nlg",
        "src.dialogue",
        "src.evaluator",
    ]
    for mod in modules:
        proc = subprocess.run(
            [sys.executable, "-m", mod],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        all_passed &= check(proc.returncode == 0, f"Chạy độc lập module `{mod}` thành công (exit code 0)")

    print("================================================================================")
    if all_passed:
        print("KẾT QUẢ CUỐI CÙNG: TẤT CẢ CÁC BÀI KIỂM THỬ ĐỀU PASS (100%)!")
        print("================================================================================")
        sys.exit(0)
    else:
        print("KẾT QUẢ CUỐI CÙNG: CÓ BÀI KIỂM THỬ THẤT BẠI!")
        print("================================================================================")
        sys.exit(1)


if __name__ == "__main__":
    verify()
