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

Danh sách từ ghép được TỰ ĐỘNG lấy từ các terminal có '_' trong models/grammar.cfg
(qua grammar_loader), nên tokenizer luôn khớp với văn phạm của Nam. Muốn thêm từ ghép
ngoài grammar -> truyền extra_compounds=['cụm từ', ...].
Ngoài ra mã chuẩn đầu ra viết 'L.O.2.5' được chuẩn hoá thành 'lo2.5' (đúng dạng trong grammar).
"""
import re
import os
import unicodedata

from src.grammar_loader import DEFAULT_GRAMMAR_PATH, grammar_terminals

# Dấu câu cần bỏ ở đầu/cuối token.
_EDGE_PUNCT = "?!.,;:\"'()[]{}…“”‘’"


class VietnameseTokenizer:
    """Tách từ + gộp từ ghép (longest match) cho câu hỏi tiếng Việt miền Course Assistant."""

    def __init__(self, grammar_path: str | None = DEFAULT_GRAMMAR_PATH,
                 extra_compounds: list[str] | None = None):
        words = list(extra_compounds or [])
        if grammar_path and os.path.exists(grammar_path):
            words += [t.replace("_", " ") for t in grammar_terminals(grammar_path) if "_" in t]
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
    def _normalize_token(tok: str) -> str:
        """'l.o.2.5' -> 'lo2.5' (dạng mã chuẩn đầu ra dùng trong grammar)."""
        m = re.fullmatch(r"l\.o\.?(\d+(?:\.\d+)*)", tok)
        return "lo" + m.group(1) if m else tok

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
                    tokens.append(VietnameseTokenizer._normalize_token(piece))
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
        "Tài liệu tham khảo về statistical NLP là gì?",
        "Có được dùng LLM/RAG không?",
        "Chương nào nói về semantic grammar?",
        "Hôm nay ở TP.HCM có mưa không?",
        "   ",
    ]
    for s in demo:
        toks = tk.tokenize(s)
        print(f"{s!r}\n   -> {toks}\n   -> {tk.detokenize(toks)!r}")
