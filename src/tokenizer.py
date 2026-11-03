"""
Tokenizer tiếng Việt dùng chung cho Phần I (Grammar / Generator / Parser).
Phụ trách: Xuân Lộc

QUY ƯỚC CHUNG CHO CẢ NHÓM (Nam viết grammar, Đức Anh parse, Nhân sinh câu):
  1. Mọi token đều là chữ thường.
  2. Từ ghép nhiều tiếng được nối bằng dấu gạch dưới '_'
     (vd: 'bài_tập_lớn', 'tín_chỉ', 'bao_nhiêu', 'semantic_grammar').
  3. Dấu câu ở đầu/cuối token bị bỏ ('?', '.', ',', '!'...). Dấu '.' nằm GIỮA token
     được giữ nguyên (vd: 'l.o.2.5', 'tp.hcm').
  4. Dấu '/' tách thành các token riêng (vd: 'llm/rag' -> 'llm', 'rag').
  5. Số giữ nguyên là token riêng ('tuần 3' -> 'tuần', '3').

Danh sách từ ghép nằm ở COMPOUND_WORDS bên dưới (viết bằng dấu cách, tự động
được ghép theo thuật toán longest-match). Muốn thêm từ ghép -> chỉ cần thêm vào
danh sách, và dùng đúng dạng có '_' trong grammar.cfg.
"""
import re
import unicodedata

# Từ ghép / cụm thuật ngữ cần gộp thành 1 token (viết thường, ngăn cách bằng dấu cách).
COMPOUND_WORDS = [
    # --- Thông tin môn học / thi cử ---
    "tín chỉ", "môn học", "bao nhiêu", "thi giữa kỳ", "thi cuối kỳ", "giữa kỳ", "cuối kỳ",
    "học kỳ", "đề cương", "chuẩn đầu ra", "nội dung", "kế hoạch", "lịch học",
    # --- Bài tập lớn / quy định / tài liệu ---
    "bài tập lớn", "bài tập", "thời hạn", "hạn nộp", "yêu cầu", "xây dựng",
    "sử dụng", "quy định", "tài liệu tham khảo", "tài liệu", "giáo trình", "tham khảo",
    "liên quan", "phương pháp",
    # --- Từ hỏi / cụm hỏi ---
    "khi nào", "ở đâu", "như thế nào", "bao lâu", "có được", "có thể", "tìm hiểu",
    # --- Thuật ngữ NLP (tiếng Anh nhiều từ) ---
    "context free grammar", "context-free grammar",
    "semantic grammar", "dependency grammar", "augmented grammar",
    "selectional restriction", "semantic network", "question answering",
    "knowledge representation", "pos tagging", "logical form", "thematic roles",
    "local discourse context", "word sense disambiguation",
    "statistical nlp", "python nlp", "top-down parsing", "bottom-up parsing",
    "chart parsing",
]

# Dấu câu cần bỏ ở đầu/cuối token.
_EDGE_PUNCT = "?!.,;:\"'()[]{}…“”‘’"


class VietnameseTokenizer:
    """Tách từ + gộp từ ghép (longest match) cho câu hỏi tiếng Việt miền Course Assistant."""

    def __init__(self, extra_compounds: list[str] | None = None):
        words = list(COMPOUND_WORDS) + list(extra_compounds or [])
        # key: tuple các tiếng -> token ghép. Vd ('bài','tập','lớn') -> 'bài_tập_lớn'
        self._compounds: dict[tuple[str, ...], str] = {}
        for w in words:
            parts = tuple(self._split_raw(self._normalize(w)))
            if len(parts) >= 2:
                self._compounds[parts] = "_".join(parts)
        self._max_len = max((len(k) for k in self._compounds), default=1)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _normalize(text: str) -> str:
        """Chuẩn hoá Unicode về NFC (tránh lệch dấu tiếng Việt), chữ thường, gọn khoảng trắng."""
        text = unicodedata.normalize("NFC", text)
        return re.sub(r"\s+", " ", text.lower()).strip()

    @staticmethod
    def _split_raw(text: str) -> list[str]:
        """Tách theo khoảng trắng, tách '/' thành token riêng, bỏ dấu câu ở biên."""
        tokens: list[str] = []
        for chunk in text.split():
            for piece in re.split(r"(/)", chunk):
                if piece == "/":
                    continue  # bỏ hẳn dấu '/', chỉ dùng làm điểm tách
                piece = piece.strip(_EDGE_PUNCT)
                if piece:
                    tokens.append(piece)
        return tokens

    # ---------------------------------------------------------------- public API
    def tokenize(self, text: str) -> list[str]:
        """
        'Bài tập lớn có mấy tín chỉ?' -> ['bài_tập_lớn', 'có', 'mấy', 'tín_chỉ']
        """
        if not text or not text.strip():
            return []
        raw = self._split_raw(self._normalize(text))

        result: list[str] = []
        i = 0
        while i < len(raw):
            matched = False
            # longest match: thử cụm dài nhất trước
            for n in range(min(self._max_len, len(raw) - i), 1, -1):
                key = tuple(raw[i:i + n])
                if key in self._compounds:
                    result.append(self._compounds[key])
                    i += n
                    matched = True
                    break
            if not matched:
                result.append(raw[i])
                i += 1
        return result

    def detokenize(self, tokens: list[str]) -> str:
        """
        ['bài_tập_lớn', 'có', 'mấy', 'tín_chỉ'] -> 'Bài tập lớn có mấy tín chỉ'
        (bỏ '_', viết hoa chữ đầu câu). Dùng cho Generator khi xuất samples.txt.
        """
        text = " ".join(tokens).replace("_", " ").strip()
        return text[:1].upper() + text[1:] if text else ""


if __name__ == "__main__":
    tk = VietnameseTokenizer()
    demo = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Bài tập lớn yêu cầu xây dựng những gì?",
        "Chương 4 học vào tuần nào?",
        "L.O.2.5 là gì?",
        "Có được dùng LLM/RAG không?",
        "Chương nào nói về semantic grammar?",
        "Hôm nay ở TP.HCM có mưa không?",
        "   ",
    ]
    for s in demo:
        toks = tk.tokenize(s)
        print(f"{s!r}\n   -> {toks}\n   -> {tk.detokenize(toks)!r}")
