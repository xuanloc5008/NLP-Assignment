"""
Phần II.2: Nhận diện Intent và Entity
Phương pháp: Classical NLP (cú pháp-dẫn xuất từ Parse Tree kết hợp Từ điển Thực thể Lexicon và Pattern Matching).
Output: output/intent-entity.txt
"""
import os
import re
from src.tokenizer import VietnameseTokenizer

class IntentEntityDetector:
    def __init__(self):
        self.tokenizer = VietnameseTokenizer()

        # Từ điển ánh xạ từ vựng / thuật ngữ sang Entity chuẩn (dựa trên data/entities.txt)
        self.topic_map = {
            "cfg": "CFG",
            "context_free_grammar": "CFG",
            "pcfg": "PCFG",
            "probabilistic_context_free_grammar": "PCFG",
            "dependency_grammar": "DEPENDENCY_GRAMMAR",
            "features": "FEATURES",
            "augmented_grammar": "AUGMENTED_GRAMMAR",
            "unification": "UNIFICATION",
            "pos_tagging": "POS_TAGGING",
            "logical_form": "LOGICAL_FORM",
            "thematic_roles": "THEMATIC_ROLES",
            "selectional_restriction": "SELECTIONAL_RESTRICTION",
            "semantic_network": "SEMANTIC_NETWORK",
            "wsd": "WSD",
            "word_sense_disambiguation": "WSD",
            "semantic_grammar": "SEMANTIC_GRAMMAR",
            "knowledge_representation": "KNOWLEDGE_REPRESENTATION",
            "question_answering": "QUESTION_ANSWERING",
            "local_discourse_context": "LOCAL_DISCOURSE_CONTEXT",
            "reference": "REFERENCE",
            "anaphora": "ANAPHORA",
            "centering": "CENTERING",
            "parsing": "PARSING",
            "parser": "PARSER",
            "statistical_nlp": "STATISTICAL_NLP",
            "python_nlp": "PYTHON_NLP",
            "hỏi_đáp": "QUESTION_ANSWERING",
            "hỏi đáp": "QUESTION_ANSWERING"
        }

    def detect(self, sentence: str, parse_tree_str: str = "()") -> tuple[str, dict]:
        """
        Nhận diện Intent và các Entity từ câu tự nhiên.
        Trả về (intent, dict_entities).
        """
        raw = sentence.strip()
        lower = raw.lower()
        toks = self.tokenizer.tokenize(raw)
        sent_norm = " ".join(toks)

        intent = "UNKNOWN"
        entities = {}

        # 1. Kiểm tra câu phụ thuộc ngữ cảnh (Context Dependent)
        if re.search(r'\b(nó|phần này|chương này|còn chương sau|nội dung này)\b', lower):
            intent = "CONTEXT_DEPENDENT"
            if "parsing" in lower:
                entities["ref_topic"] = "PARSING"
            if "xuất file" in lower or "file" in lower:
                entities["ref_target"] = "OUTPUT_FILES"
            if "chương sau" in lower:
                entities["ref_dir"] = "NEXT_CHAPTER"
            return intent, entities

        # 2. Nhóm hỏi chuẩn đầu ra (GET_LO)
        m_lo = re.search(r'\blo(\d+(?:\.\d+)?)\b', sent_norm) or re.search(r'l\.?o\.?\s*(\d+(?:\.\d+)?)', lower)
        if m_lo:
            intent = "GET_LO"
            lo_num = m_lo.group(1)
            entities["lo"] = f"LO{lo_num}"
            entities["primary"] = f"LO{lo_num}"
            return intent, entities

        # 3. Nhóm hỏi thời gian thi cử (GET_COURSE_INFO)
        if "midterm" in lower or "thi_giữa_kỳ" in sent_norm or "giữa kỳ" in lower:
            intent = "GET_COURSE_INFO"
            entities["exam"] = "MIDTERM"
            entities["primary"] = "MIDTERM"
            return intent, entities

        if "final" in lower or "thi_cuối_kỳ" in sent_norm or "cuối kỳ" in lower:
            intent = "GET_COURSE_INFO"
            entities["exam"] = "FINAL"
            entities["primary"] = "FINAL"
            return intent, entities

        # 4. Nhóm hỏi thông tin môn học (GET_COURSE_INFO)
        if "tín_chỉ" in sent_norm or "tín chỉ" in lower:
            intent = "GET_COURSE_INFO"
            entities["metric"] = "CREDITS"
            entities["course"] = "CO3085"
            entities["primary"] = "CO3085"
            return intent, entities

        if any(p in lower for p in ["mấy phần", "những phần nào", "các phần nào", "gồm những phần"]):
            intent = "GET_COURSE_INFO"
            entities["metric"] = "PARTS"
            entities["course"] = "CO3085"
            entities["primary"] = "CO3085"
            return intent, entities

        # 5. Nhóm hỏi hạn nộp / Deadline (GET_DEADLINE)
        if "deadline" in lower or "hạn nộp" in lower or "thời hạn" in lower:
            intent = "GET_DEADLINE"
            entities["assignment"] = "BTL01"
            entities["primary"] = "PROJECT"
            return intent, entities

        # 6. Nhóm hỏi bài tập lớn (GET_ASSIGNMENT)
        if "bài_tập_lớn" in sent_norm or "bài tập lớn" in lower or "btl" in lower:
            intent = "GET_ASSIGNMENT"
            if "phần i" in lower or "phần 1" in lower or "parser" in lower:
                entities["part"] = "PART_I"
                entities["primary"] = "PART_I"
            elif "phần ii" in lower or "phần 2" in lower or "hỏi đáp" in lower or "hỏi_đáp" in sent_norm:
                entities["part"] = "PART_II"
                entities["primary"] = "PART_II"
            elif "phần iii" in lower or "phần 3" in lower:
                entities["part"] = "PART_III"
                entities["primary"] = "PART_III"
            else:
                entities["assignment"] = "BTL01"
                entities["primary"] = "BTL01"
            return intent, entities

        # 7. Nhóm hỏi quy định & chính sách AI (GET_RULE)
        if any(term in sent_norm for term in ["llm", "rag", "chatgpt"]) or "công cụ ai" in lower or "sử dụng ai" in lower or "quy định về ai" in lower or "dùng ai" in lower:
            intent = "GET_RULE"
            if "llm" in sent_norm or "rag" in sent_norm:
                entities["rule_topic"] = "LLM_RAG"
                entities["primary"] = "LLM_RAG"
            else:
                entities["rule_topic"] = "AI_USAGE"
                entities["primary"] = "AI_USAGE"
            return intent, entities

        # 8. Nhóm hỏi tài liệu tham khảo (GET_RESOURCE)
        if "tài_liệu" in sent_norm or "tài liệu" in lower or "giáo trình" in lower or "sách" in lower:
            intent = "GET_RESOURCE"
            if "statistical" in lower:
                entities["resource_topic"] = "STATISTICAL_NLP"
                entities["primary"] = "STATISTICAL_NLP"
            elif "python" in lower:
                entities["resource_topic"] = "PYTHON_NLP"
                entities["primary"] = "PYTHON_NLP"
            else:
                found_topic = None
                for term, code in self.topic_map.items():
                    if term in sent_norm or term.replace("_", " ") in lower:
                        found_topic = code
                        break
                entities["resource_topic"] = found_topic or "GENERAL"
                entities["primary"] = found_topic or "GENERAL"
            return intent, entities

        # 9. Nhóm hỏi lịch học (GET_SCHEDULE)
        m_week = re.search(r'tuần\s*(\d+)', lower)
        if m_week and ("học" in lower or "gì" in lower or "lịch" in lower):
            intent = "GET_SCHEDULE"
            w_num = int(m_week.group(1))
            entities["week"] = f"WEEK_{w_num:02d}"
            entities["primary"] = f"WEEK_{w_num:02d}"
            return intent, entities

        m_ch = re.search(r'chương\s*(\d+)', lower)
        if m_ch and ("vào tuần nào" in lower or "tuần nào" in lower):
            intent = "GET_SCHEDULE"
            ch_num = int(m_ch.group(1))
            entities["chapter"] = f"CH{ch_num:02d}"
            entities["primary"] = f"CH{ch_num:02d}"
            return intent, entities

        # 10. Nhóm hỏi chủ đề kiến thức (GET_TOPIC)
        if m_ch:
            intent = "GET_TOPIC"
            ch_num = int(m_ch.group(1))
            entities["chapter"] = f"CH{ch_num:02d}"
            entities["primary"] = f"CH{ch_num:02d}"
            # Xem có hỏi về topic cụ thể trong chương không
            for term, code in self.topic_map.items():
                if term in sent_norm or term.replace("_", " ") in lower:
                    entities["sub_topic"] = code
            return intent, entities

        # Tìm chủ đề được hỏi: "Chương nào nói về CFG?", "PCFG học ở đâu?"
        for term, code in self.topic_map.items():
            if term in sent_norm or term.replace("_", " ") in lower:
                if any(w in lower for w in ["chương nào", "ở đâu", "học ở", "nói về"]):
                    intent = "GET_TOPIC"
                    entities["topic"] = code
                    entities["primary"] = code
                    return intent, entities

        # 11. Ngoài miền bài toán (OUT_OF_SCOPE)
        intent = "UNKNOWN"
        entities["primary"] = "OUT_OF_SCOPE"
        entities["scope"] = "OUT_OF_SCOPE"
        return intent, entities

    def process_file(self, input_path: str, output_path: str):
        """Xử lý từng dòng câu hỏi đầu vào và ghi ra file intent-entity.txt"""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(input_path, "r", encoding="utf-8") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:
            for line in fin:
                s = line.strip()
                if not s:
                    continue
                intent, entities = self.detect(s)
                ent_items = [f"{k}={v}" for k, v in entities.items() if k != "primary"]
                ent_str = ", ".join(ent_items) if ent_items else entities.get("primary", "NONE")
                fout.write(f"INTENT: {intent} | ENTITIES: [{ent_str}]\n")

if __name__ == "__main__":
    detector = IntentEntityDetector()
    sample_queries = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học gì?",
        "Chương nào nói về CFG?",
        "L.O.2.5 là gì?",
        "Có được dùng LLM/RAG không?",
        "Hôm nay ở TP.HCM có mưa không?"
    ]
    for q in sample_queries:
        it, et = detector.detect(q)
        print(f"Query: {q}\n  -> Intent: {it}, Entities: {et}")
