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
            num_map = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V'}
            roman = num_map.get(val, val.upper())
            return f"PART_{roman}"

        elif tag == 'ASSIGN_PART':
            if val in ['parser', 'grammar', 'ngữ_pháp', 'phân_tích_cú_pháp']:
                return 'PART_I'
            elif val in ['hỏi_đáp', 'qa', 'semantic', 'diễn_dịch_ngữ_nghĩa']:
                return 'PART_II'
            elif val in ['ngữ_cảnh']:
                return 'PART_III'
            elif val in ['đánh_giá', 'evaluation']:
                return 'PART_IV'
            return val.upper()

        elif tag in ['RULE_TERM', 'AI_TERM']:
            if val in ['ai', 'trí_tuệ_nhân_tạo', 'chatgpt']:
                return 'AI_USAGE'
            if val in ['llm', 'rag', 'llm_rag', 'llm rag']:
                return 'LLM_RAG'
            if val in ['điểm_danh', 'tham_dự_lớp']:
                return 'ATTENDANCE'
            if val in ['liêm_chính_học_thuật']:
                return 'ACADEMIC_INTEGRITY'
            if val in ['chia_sẻ_bài_làm', 'sao_chép_code']:
                return 'ASSIGNMENT_SHARING'
            if val in ['thư_viện_bên_ngoài']:
                return 'EXTERNAL_LIBRARIES'
            if val in ['mã_nguồn']:
                return 'SOURCE_CODE'
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

    def from_semantic(self, semantic_str: str) -> tuple[str, dict]:
        """
        Ánh xạ trực tiếp từ biểu diễn ngữ nghĩa vị từ (Semantic Representation, vd: GET_CREDIT(course=CO3085))
        sang (Intent, Entities).
        """
        if not semantic_str or semantic_str.strip() in ("", "UNKNOWN()"):
            return "UNKNOWN", {"status": "OUT_OF_SCOPE"}

        m = re.match(r"^([A-Z_]+)\((.*)\)$", semantic_str.strip())
        if not m:
            return "UNKNOWN", {"status": "OUT_OF_SCOPE"}

        pred, args_str = m.group(1), m.group(2).strip()
        pred_to_intent = {
            "GET_CREDIT": "GET_COURSE_INFO",
            "GET_EXAM_INFO": "GET_COURSE_INFO",
            "GET_COURSE_INFO": "GET_COURSE_INFO",
            "GET_SCHEDULE": "GET_SCHEDULE",
            "GET_TOPIC": "GET_TOPIC",
            "GET_DEADLINE": "GET_DEADLINE",
            "GET_ASSIGNMENT": "GET_ASSIGNMENT",
            "GET_RULE": "GET_RULE",
            "GET_RESOURCE": "GET_RESOURCE",
            "GET_LO": "GET_LO",
            "GET_CONTEXT_DEPENDENT_INFO": "CONTEXT_DEPENDENT",
        }
        intent = pred_to_intent.get(pred, "UNKNOWN")
        entities = {}
        if args_str:
            for pair in args_str.split(","):
                if "=" in pair:
                    k, v = [x.strip() for x in pair.split("=", 1)]
                    if k == "course":
                        entities["course"] = v
                    elif k == "week":
                        entities["week"] = v
                    elif k == "chapter":
                        entities["chapter"] = v
                    elif k == "topic":
                        if intent == "GET_RULE":
                            entities["rule_term"] = v
                        elif intent == "GET_RESOURCE":
                            entities["resource_topic"] = v
                        else:
                            entities["topic"] = self.normalize_entity("TOPIC_EN", v)
                    elif k == "exam":
                        entities["exam"] = v
                    elif k == "lo":
                        entities["lo_code"] = v
                    elif k == "assignment":
                        entities["assignment_id"] = "BTL01" if v == "PROJECT" else v
                    elif k == "part":
                        entities["assignment_part"] = self.normalize_entity(
                            "PART_NUM" if v in ("I", "II", "III", "IV", "1", "2", "3", "4") else "ASSIGN_PART",
                            v,
                        )
        return intent, entities

    def detect(self, parse_tree_str: str, semantic_str: str = "") -> tuple[str, dict]:
        """
        Nhận vào chuỗi cây cú pháp (Syntactic Representation) và/hoặc biểu diễn ngữ nghĩa
        (Semantic Representation), trả về (intent, dict_entities).
        """
        intent = "UNKNOWN"
        entities = {}

        if semantic_str:
            sem_intent, sem_entities = self.from_semantic(semantic_str)
            if sem_intent != "UNKNOWN":
                intent = sem_intent
                entities.update(sem_entities)

        if not parse_tree_str:
            return intent, (entities if entities else {'status': 'OUT_OF_SCOPE'})

        text_str = parse_tree_str.strip()
        if not text_str.startswith('('):
            text_str = self._get_parser().parse_sentence(text_str)

        # 1. Xử lý câu ngoài phạm vi (Parser trả về "()")
        if not text_str or text_str.strip() == '()':
            return "UNKNOWN", {'status': 'OUT_OF_SCOPE'}

        # 2. Trích xuất Intent từ node cấp 1 ngay dưới S
        intent_match = re.search(r'\(S \((Q_[A-Z_]+)', text_str)
        if intent_match:
            intent = self.intent_mapping.get(intent_match.group(1), intent)

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

    def process_file(self, input_path: str, output_path: str, semantic_path: str = None):
        """
        Đọc kết quả từ Syntactic Representation (output/parse-results.txt) kết hợp với
        Semantic Interpretation (output/semantic.txt) và xuất ra output/intent-entity.txt.
        """
        if not os.path.exists(input_path):
            print(f"[Lỗi] Không tìm thấy file {input_path}")
            return

        if semantic_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            default_sem = os.path.join(project_root, "output", "semantic.txt")
            if os.path.exists(default_sem):
                semantic_path = default_sem

        with open(input_path, 'r', encoding='utf-8') as f:
            parse_trees = f.read().splitlines()

        semantic_lines = []
        if semantic_path and os.path.exists(semantic_path):
            with open(semantic_path, 'r', encoding='utf-8') as f:
                semantic_lines = f.read().splitlines()

        results = []
        for idx, tree in enumerate(parse_trees):
            sem_str = semantic_lines[idx] if idx < len(semantic_lines) else ""
            intent, entities = self.detect(tree, semantic_str=sem_str)
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
