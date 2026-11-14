"""
Phần II.1: Xây dựng biểu diễn ngữ nghĩa (Semantic Representation)
Phụ trách: Đinh Hải Nam (Mục 4.1.1)
Output yêu cầu: output/semantic.txt (dạng logic/vị từ: GET_CREDIT(course=CO3085), GET_SCHEDULE(week=WEEK_03)...)
"""

import os
import re
from nltk import Tree
from src.parser import CourseParser

class SemanticInterpreter:
    def __init__(self, entities_path: str = None):
        self.default_course = "CO3085"
        self.default_assignment = "PROJECT"
        self.entity_map = {}

        if entities_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            entities_path = os.path.join(project_root, "data", "entities.txt")
        if entities_path and os.path.exists(entities_path):
            self._load_entities(entities_path)

    def _load_entities(self, filepath: str):
        """Đọc file data/entities.txt để xây dựng từ điển chuẩn hóa thực thể."""
        current_section = None
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('='):
                    continue
                
                if '=' not in line:
                    current_section = line
                    continue
                
                left, right = [x.strip() for x in line.split('=', 1)]
                left_norm = left.lower().replace(' ', '_')
                right_vals = [x.strip().lower().replace(' ', '_') for x in right.split('/')]
                
                if current_section == "COURSE":
                    self.entity_map[left_norm] = "CO3085"
                    for rv in right_vals:
                        self.entity_map[rv] = "CO3085"
                        
                elif current_section == "CHAPTERS":
                    num_match = re.search(r'\d+', left)
                    if num_match:
                        ch_num = int(num_match.group())
                        std_ch = f"CH{ch_num:02d}"
                        self.entity_map[str(ch_num)] = std_ch
                        self.entity_map[f"chương_{ch_num}"] = std_ch
                        
                else: 
                    self.entity_map[left_norm] = left
                    for rv in right_vals:
                        if rv not in self.entity_map:
                            self.entity_map[rv] = left

    def _normalize_entity(self, label: str, raw_val: str) -> str:
        """Chuẩn hóa token từ Parser dựa vào từ điển entities.txt."""
        raw_val_lower = raw_val.lower()

        if label == 'COURSE_NAME':
            return self.default_course
        elif label == 'WEEK_NUM':
            return f"WEEK_{int(raw_val):02d}" if raw_val.isdigit() else raw_val.upper()
        elif label == 'CH_NUM':
            return f"CH{int(raw_val):02d}" if raw_val.isdigit() else raw_val.upper()

        if raw_val_lower in self.entity_map:
            return self.entity_map[raw_val_lower]

        return raw_val.upper()

    def interpret(self, sentence: str, parse_tree_str: str = "") -> str:
        """Ánh xạ cây cú pháp sang biểu diễn ngữ nghĩa dạng vị từ."""
        if not parse_tree_str or parse_tree_str == "()":
            return "UNKNOWN()"

        try:
            tree = Tree.fromstring(parse_tree_str)
        except ValueError:
            return "UNKNOWN()"

        if tree.label() == 'S' and len(tree) > 0:
            intent_node = tree[0]
            intent_label = intent_node.label()
        else:
            return "UNKNOWN()"

        entities = {}
        for subtree in intent_node.subtrees():
            label = subtree.label()
            if not isinstance(label, str): 
                continue
            
            leaves = subtree.leaves()
            if not leaves: 
                continue
                
            raw_val = leaves[0]
            norm_val = self._normalize_entity(label, raw_val)

            if label == 'COURSE_NAME':
                entities['course'] = norm_val
            elif label == 'COURSE_METRIC':
                entities['metric'] = norm_val
            elif label == 'WEEK_NUM' and 'week' not in entities:
                entities['week'] = norm_val
            elif label == 'CH_NUM' and 'chapter' not in entities and 'week' not in entities:
                entities['chapter'] = norm_val
            elif label in ['TOPIC_ENTITY', 'TOPIC_ABBR', 'TOPIC_EN', 'TOPIC_VI', 'RES_TOPIC']:
                if 'topic' not in entities:
                    entities['topic'] = norm_val
            elif label == 'EXAM':
                entities['exam'] = norm_val
            elif label == 'LO_CODE':
                entities['lo'] = norm_val
            elif label in ['ASSIGN_PART', 'PART_NUM']:
                entities['assign_part'] = norm_val
            elif label in ['RULE_TERM', 'AI_TERM']:
                entities['rule'] = 'AI_USAGE' if norm_val == 'AI' else norm_val

        if intent_label == 'Q_COURSE_INFO':
            metric = entities.get('metric', '')
            course = entities.get('course', self.default_course)
            if metric == 'TÍN_CHỈ':
                return f"GET_CREDIT(course={course})"
            elif 'exam' in entities:
                return f"GET_EXAM_INFO(exam={entities['exam']})"
            else:
                return f"GET_COURSE_INFO(course={course})"

        elif intent_label == 'Q_SCHEDULE':
            if 'week' in entities:
                return f"GET_SCHEDULE(week={entities['week']})"
            elif 'chapter' in entities:
                return f"GET_SCHEDULE(chapter={entities['chapter']})"
            return "GET_SCHEDULE()"

        elif intent_label == 'Q_TOPIC':
            args = []
            if 'chapter' in entities:
                args.append(f"chapter={entities['chapter']}")
            if 'topic' in entities:
                args.append(f"topic={entities['topic']}")
            
            args_str = ", ".join(args)
            return f"GET_TOPIC({args_str})"

        elif intent_label == 'Q_DEADLINE':
            return f"GET_DEADLINE(assignment={self.default_assignment})"

        elif intent_label == 'Q_ASSIGNMENT':
            part = entities.get('assign_part', '')
            if part:
                return f"GET_ASSIGNMENT(assignment={self.default_assignment}, part={part})"
            return f"GET_ASSIGNMENT(assignment={self.default_assignment})"

        elif intent_label == 'Q_RULE':
            if 'rule' in entities:
                return f"GET_RULE(topic={entities['rule']})"
            return "GET_RULE()"

        elif intent_label == 'Q_RESOURCE':
            if 'topic' in entities:
                return f"GET_RESOURCE(topic={entities['topic']})"
            return "GET_RESOURCE()"

        elif intent_label == 'Q_LO':
            lo = entities.get('lo', '')
            return f"GET_LO(lo={lo})"

        elif intent_label == 'Q_CONTEXT':
            return "GET_CONTEXT_DEPENDENT_INFO()"

        return "UNKNOWN()"

    def process_file(self, input_path: str, output_path: str, parse_results_path: str = None):
        """
        Nhận Syntactic Representation từ output/parse-results.txt (hoặc phân tích từ input/sentences.txt
        nếu chạy độc lập) và ánh xạ sang biểu diễn ngữ nghĩa vị từ tại output/semantic.txt.
        Pipeline: Natural Language Input -> Grammar/Parser -> Syntactic Representation -> Semantic Interpretation
        """
        if not os.path.exists(input_path):
            print(f"Lỗi: Không tìm thấy file {input_path}.")
            return

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parse_results_path is None:
            default_parse = os.path.join(project_root, "output", "parse-results.txt")
            if os.path.exists(default_parse):
                parse_results_path = default_parse

        with open(input_path, 'r', encoding='utf-8') as f:
            sentences = f.read().splitlines()

        if parse_results_path and os.path.exists(parse_results_path):
            with open(parse_results_path, 'r', encoding='utf-8') as f:
                parse_trees = f.read().splitlines()
        else:
            grammar_path = os.path.join(project_root, "models", "grammar.cfg")
            parser = CourseParser(grammar_path)
            parse_trees = [parser.parse_sentence(s) for s in sentences]

        results = []
        for idx, sentence in enumerate(sentences):
            tree_str = parse_trees[idx] if idx < len(parse_trees) else "()"
            semantic_rep = self.interpret(sentence=sentence, parse_tree_str=tree_str)
            results.append(semantic_rep)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(r + "\n")
                
        success_count = sum(1 for r in results if r != "UNKNOWN()")
        print(f"-> Đã trích xuất ngữ nghĩa thành công cho {success_count}/{len(sentences)} câu, lưu vào {output_path}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    entities_path = os.path.join(root, "data", "entities.txt")
    interpreter = SemanticInterpreter(entities_path=entities_path)
    
    # Chỉ cung cấp đúng đường dẫn file input/sentences.txt và file đích output/semantic.txt
    interpreter.process_file(
        input_path=os.path.join(root, "input", "sentences.txt"),
        output_path=os.path.join(root, "output", "semantic.txt")
    )