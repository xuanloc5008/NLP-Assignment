"""
Script Kiểm thử Toàn diện Hệ thống (Automated Verification Suite)
Chạy script này để kiểm tra xem đồ án đã đạt 100% tiêu chí đề bài chưa:
  1. Xóa sạch thư mục output/
  2. Kích hoạt toàn bộ pipeline: python3 -m src.main
  3. Kiểm định từng file output theo quy chuẩn đề bài:
     - Số dòng phải khớp chính xác với input/sentences.txt
     - Cú pháp cây cú pháp hoặc '()'
     - Fallback message câu ngoài phạm vi
     - Định dạng hội thoại 4 trường
     - Báo cáo đánh giá đầy đủ chỉ số
  4. Kiểm tra đóng gói file ZIP (< 10MB)
"""
import os
import shutil
import subprocess
import sys
import zipfile

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(PROJECT_ROOT, "input", "sentences.txt")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

FALLBACK_MSG = "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu của môn học."

def count_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def main():
    print("=" * 75)
    print("BẮT ĐẦU KIỂM THỬ TOÀN DIỆN ASSIGNMENT (AUTOMATED GRADING SIMULATION)")
    print("=" * 75)

    # 1. Đếm số câu input
    input_lines = count_lines(INPUT_FILE)
    num_queries = len(input_lines)
    print(f"\n[BƯỚC 1] File input/sentences.txt có: {num_queries} câu hỏi.")

    # 2. Xóa output cũ để bảo đảm kết quả sinh hoàn toàn động
    print("\n[BƯỚC 2] Xóa sạch thư mục output/ cũ để giả lập môi trường chấm bài...")
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            fpath = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(fpath):
                os.remove(fpath)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 3. Chạy pipeline chính
    print("\n[BƯỚC 3] Kích hoạt pipeline chính (python -m src.main)...")
    res = subprocess.run([sys.executable, "-m", "src.main"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print("[FAIL] Pipeline bị lỗi khi chạy:")
        print(res.stderr)
        return False
    print("[PASS] Pipeline thực thi thành công không có ngoại lệ.")

    # 4. Kiểm tra từng file output theo yêu cầu đề bài
    print("\n[BƯỚC 4] Kiểm định quy chuẩn 9 file output theo đặc tả đề bài:")
    checks = []

    def log_check(name, passed, detail):
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name:<22} : {detail}")
        checks.append(passed)

    # 4.1 grammar.txt
    f_grammar = os.path.join(OUTPUT_DIR, "grammar.txt")
    passed = os.path.exists(f_grammar) and os.path.getsize(f_grammar) > 0
    log_check("output/grammar.txt", passed, "Tồn tại và chứa tập luật CFG")

    # 4.2 samples.txt
    f_samples = os.path.join(OUTPUT_DIR, "samples.txt")
    s_lines = count_lines(f_samples) if os.path.exists(f_samples) else []
    passed = 0 < len(s_lines) <= 10000 and len(s_lines) == len(set(s_lines))
    log_check("output/samples.txt", passed, f"{len(s_lines)} câu sinh hợp lệ, không trùng lặp (<= 10.000)")

    # 4.3 parse-results.txt
    f_parse = os.path.join(OUTPUT_DIR, "parse-results.txt")
    p_lines = count_lines(f_parse) if os.path.exists(f_parse) else []
    passed_lines = len(p_lines) == num_queries
    passed_format = all(p == "()" or (p.startswith("(S") and p.endswith(")")) for p in p_lines)
    log_check("output/parse-results.txt", passed_lines and passed_format, f"{len(p_lines)}/{num_queries} dòng khớp input, định dạng cây chuẩn hoặc ()")

    # 4.4 semantic.txt
    f_sem = os.path.join(OUTPUT_DIR, "semantic.txt")
    sem_lines = count_lines(f_sem) if os.path.exists(f_sem) else []
    passed = len(sem_lines) == num_queries and any("GET_" in l for l in sem_lines)
    log_check("output/semantic.txt", passed, f"{len(sem_lines)}/{num_queries} dòng biểu diễn logic / vị từ")

    # 4.5 intent-entity.txt
    f_ie = os.path.join(OUTPUT_DIR, "intent-entity.txt")
    ie_lines = count_lines(f_ie) if os.path.exists(f_ie) else []
    passed = len(ie_lines) == num_queries and all("INTENT:" in l for l in ie_lines)
    log_check("output/intent-entity.txt", passed, f"{len(ie_lines)}/{num_queries} dòng nhận diện Intent & Entity")

    # 4.6 query.txt
    f_q = os.path.join(OUTPUT_DIR, "query.txt")
    q_lines = count_lines(f_q) if os.path.exists(f_q) else []
    passed = len(q_lines) == num_queries
    log_check("output/query.txt", passed, f"{len(q_lines)}/{num_queries} dòng câu truy vấn hướng tới KB")

    # 4.7 answer.txt
    f_ans = os.path.join(OUTPUT_DIR, "answer.txt")
    ans_lines = count_lines(f_ans) if os.path.exists(f_ans) else []
    passed_count = len(ans_lines) == num_queries
    has_fallback = any(l == FALLBACK_MSG for l in ans_lines)
    log_check("output/answer.txt", passed_count and has_fallback, f"{len(ans_lines)}/{num_queries} dòng, có xử lý fallback out-of-scope đúng quy định")

    # 4.8 dialogue.txt
    f_dlg = os.path.join(OUTPUT_DIR, "dialogue.txt")
    dlg_content = open(f_dlg, encoding="utf-8").read().lower() if os.path.exists(f_dlg) else ""
    passed_dlg = all(kw in dlg_content for kw in [
        "hội thoại đầu vào",
        "thông tin ngữ cảnh",
        "kết quả diễn giải",
        "câu trả lời"
    ])
    log_check("output/dialogue.txt", passed_dlg, "Đầy đủ 4 trường thông tin cho hội thoại ngữ cảnh")

    # 4.9 evaluation.txt
    f_eval = os.path.join(OUTPUT_DIR, "evaluation.txt")
    eval_content = open(f_eval, encoding="utf-8").read().lower() if os.path.exists(f_eval) else ""
    passed_eval = all(kw in eval_content for kw in [
        "độ chính xác",
        "phân tích nguyên nhân",
        "ưu điểm và hạn chế"
    ])
    log_check("output/evaluation.txt", passed_eval, "Báo cáo có đủ số đo, phân tích lỗi, ưu/nhược điểm")

    # 5. Kiểm tra đóng gói ZIP < 10MB
    print("\n[BƯỚC 5] Thử nghiệm đóng gói nén ZIP dự án:")
    zip_path = os.path.join(PROJECT_ROOT, "test_check.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            if any(x in root for x in ['venv', '.git', '__pycache__']):
                continue
            for file in files:
                if file in ['.DS_Store', 'test_check.zip']:
                    continue
                fpath = os.path.join(root, file)
                zf.write(fpath, arcname=os.path.relpath(fpath, PROJECT_ROOT))
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    passed_zip = zip_size_mb < 10.0
    log_check("Dung lượng ZIP", passed_zip, f"{zip_size_mb:.2f} MB (Quy định đề bài: < 10MB)")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Tổng kết
    print("\n" + "=" * 75)
    if all(checks):
        print("KẾT QUẢ: 100% TẤT CẢ TIÊU CHÍ KIỂM THỬ ĐỀU ĐẠT CHUẨN [PASS]!")
        print("Đồ án hoàn toàn sẵn sàng để nộp bài và chạy chấm điểm.")
    else:
        print("KẾT QUẢ: VẪN CÒN TIÊU CHÍ [FAIL]. Vui lòng rà soát lại thông báo ở trên.")
    print("=" * 75)
    return all(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
