"""
Phần II.2: Nhận diện Intent và Entity
Phụ trách: Thành Nhân (Mục 4.1.2)
Output yêu cầu: output/intent-entity.txt
Phương pháp: Rule-based trên Parse Tree kết hợp chuẩn hóa Lexicon từ entities.txt
"""

import os
import re


class IntentEntityDetector:
    def __init__(self, data_dir: str = "data"):
        self.valid_intents = [
            'GET_COURSE_INFO', 'GET_SCHEDULE', 'GET_TOPIC',
            'GET_ASSIGNMENT', 'GET_DEADLINE', 'GET_RESOURCE',
            'GET_RULE', 'GET_LO', 'CONTEXT_DEPENDENT', 'UNKNOWN'
        ]

        self.intent_mapping = {
            'Q_COURSE_INFO': 'GET_COURSE_INFO',
            'Q_SCHEDULE': 'GET_SCHEDULE',
            'Q_TOPIC': 'GET_TOPIC',
            'Q_ASSIGNMENT': 'GET_ASSIGNMENT',
            'Q_DEADLINE': 'GET_DEADLINE',
            'Q_RESOURCE': 'GET_RESOURCE',
            'Q_RULE': 'GET_RULE',
            'Q_LO': 'GET_LO',
            'Q_CONTEXT': 'CONTEXT_DEPENDENT'
        }

        self.entity_tags = [
            'COURSE_NAME', 'WEEK_NUM', 'CH_NUM', 'PART_NUM',
            'ASSIGN_PART', 'RULE_TERM', 'AI_TERM', 'LO_CODE', 'EXAM',
            'TOPIC_ABBR', 'TOPIC_EN', 'TOPIC_VI', 'RES_TOPIC', 'CTX_REF', 'CTX_DIR'
        ]
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.grammar_path = os.path.join(project_root, "models", "grammar.cfg")
        self._parser = None
        # Load lexicon từ entities.txt
        self.lexicon = {}
        self.vi_to_en_lexicon = {}
        self._load_entities(data_dir)

    def _get_parser(self):
        if self._parser is None:
            from src.parser import CourseParser
            self._parser = CourseParser(self.grammar_path)
        return self._parser

    def _load_entities(self, data_dir: str):
        # Đọc và ánh xạ các thực thể từ file entities.txt
        filepath = os.path.join(data_dir, "entities.txt")
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        for line in lines:
            if '=' in line:
                left, right = line.split('=', 1)
                key = left.strip().lower()
                val = right.strip().lower()
                self.lexicon[key] = right.strip()
                self.vi_to_en_lexicon[val] = left.strip().upper().replace(' ', '_')

    def _clean_leaf_value(self, raw_str: str) -> str:
        """
        Xóa các tên thẻ IN HOA lồng nhau (kể cả thẻ có dấu _ như CH_NUM)
        và dấu ngoặc, giữ nguyên dấu _ của từ ghép viết thường
        """
        cleaned = re.sub(r'\(?[A-Z][A-Z0-9_]*\s*|\)', '', raw_str)
        return cleaned.strip()

    def normalize_entity(self, tag: str, raw_value: str) -> str:
        # Chuẩn hóa giá trị thô về Lexicon ID
        val = raw_value.lower().strip()

        if tag == 'COURSE_NAME':
            if val in ['nlp', 'co3085', 'natural_language_processing', 'xử_lý_ngôn_ngữ_tự_nhiên']:
                return 'CO3085'
            return val.upper()

        elif tag == 'CH_NUM':
            return f"CH{int(val):02d}"

        elif tag == 'WEEK_NUM':
            return f"WEEK_{int(val):02d}"

        elif tag == 'PART_NUM':
            return f"PART_{val.upper()}"

        elif tag == 'ASSIGN_PART':
            if val in ['parser', 'grammar']:
                return 'PART_I'
            elif val in ['hỏi_đáp', 'qa', 'semantic']:
                return 'PART_II'
            return val.upper()

        elif tag in ['RULE_TERM', 'AI_TERM']:
            if val in ['ai', 'trí_tuệ_nhân_tạo']:
                return 'AI_USAGE'
            if val in ['llm', 'rag', 'llm_rag', 'llm rag']:
                return 'LLM_RAG'
            return val.upper()

        elif tag in ['TOPIC_ABBR', 'TOPIC_EN', 'TOPIC_VI', 'RES_TOPIC']:
            val_space = val.replace('_', ' ')
            if val_space in self.vi_to_en_lexicon:
                return self.vi_to_en_lexicon[val_space]
            return val.upper()

        elif tag in ['LO_CODE', 'EXAM']:
            return val.upper()

        elif tag in ['CTX_REF', 'CTX_DIR']:
            return val.replace('_', ' ')

        return val

    def detect(self, parse_tree_str: str) -> tuple[str, dict]:
        """Nhận vào chuỗi cây cú pháp hoặc câu tiếng Việt thô, trả về (intent, dict_entities)"""
        intent = "UNKNOWN"
        entities = {}

        if not parse_tree_str:
            return intent, {'status': 'OUT_OF_SCOPE'}

        text_str = parse_tree_str.strip()
        if not text_str.startswith('('):
            text_str = self._get_parser().parse_sentence(text_str)

        # 1. Xử lý câu ngoài phạm vi (Parser trả về "()")
        if not text_str or text_str.strip() == '()':
            return intent, {'status': 'OUT_OF_SCOPE'}

        # 2. Trích xuất Intent từ node cấp 1 ngay dưới S
        intent_match = re.search(r'\(S \((Q_[A-Z_]+)', text_str)
        if intent_match:
            intent = self.intent_mapping.get(intent_match.group(1), "UNKNOWN")

        # 3. Trích xuất và chuẩn hóa Entities
        tree_without_week = re.sub(r'\(WEEK_NUM\s+\(CH_NUM\s+[^\)]+\)\)', '', text_str)
        for tag in self.entity_tags:
            search_str = tree_without_week if tag == 'CH_NUM' else text_str
            pattern = r'\(' + tag + r'\s+([^\)]+)\)'
            matches = re.findall(pattern, search_str)

            if matches:
                clean_values = [self._clean_leaf_value(v) for v in matches]
                raw_val = clean_values[0]
                norm_val = self.normalize_entity(tag, raw_val)

                if tag in ['TOPIC_ABBR', 'TOPIC_EN', 'TOPIC_VI']:
                    entities['topic'] = norm_val
                elif tag == 'CH_NUM':
                    entities['chapter'] = norm_val
                elif tag == 'WEEK_NUM':
                    entities['week'] = norm_val
                elif tag == 'COURSE_NAME':
                    entities['course'] = norm_val
                elif tag == 'LO_CODE':
                    entities['lo_code'] = norm_val
                elif tag == 'RES_TOPIC':
                    entities['resource_topic'] = norm_val
                elif tag == 'EXAM':
                    entities['exam'] = norm_val
                elif tag in ['RULE_TERM', 'AI_TERM']:
                    entities['rule_term'] = norm_val
                elif tag in ['PART_NUM', 'ASSIGN_PART']:
                    entities['assignment_part'] = norm_val
                elif tag in ['CTX_REF', 'CTX_DIR']:
                    entities['context_ref'] = norm_val
                else:
                    entities[tag.lower()] = norm_val

        # 4. Gán mã BTL01 nếu câu hỏi nhắc đến bài tập lớn
        if 'bài_tập_lớn' in text_str and 'assignment_id' not in entities:
            entities['assignment_id'] = 'BTL01'
        if intent == 'GET_COURSE_INFO' and 'exam' not in entities and 'course' not in entities:
            entities['course'] = 'CO3085'

        return intent, entities

    def process_file(self, input_path: str, output_path: str):
        """Đọc kết quả từ output/parse-results.txt và xuất ra output/intent-entity.txt"""
        if not os.path.exists(input_path):
            print(f"[Lỗi] Không tìm thấy file {input_path}")
            return

        with open(input_path, 'r', encoding='utf-8') as f:
            parse_trees = f.read().splitlines()

        results = []
        for tree in parse_trees:
            intent, entities = self.detect(tree)
            results.append(f"{intent} | {entities}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(r + "\n")

        print(f"-> Đã trích xuất và chuẩn hóa Intent/Entity cho {len(results)} câu vào {output_path}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    detector = IntentEntityDetector(data_dir=os.path.join(root, "data"))

    input_file = os.path.join(root, "output", "parse-results.txt")
    output_file = os.path.join(root, "output", "intent-entity.txt")

    detector.process_file(input_file, output_file)
