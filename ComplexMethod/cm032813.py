def __call__(self, filename, binary=None, from_page=0, to_page=100000):
        self.doc = Document(filename) if not binary else Document(BytesIO(binary))
        pn = 0
        lines = []
        level_set = set()
        bull = bullets_category([p.text for p in self.doc.paragraphs])
        for p in self.doc.paragraphs:
            if pn > to_page:
                break
            question_level, p_text = docx_question_level(p, bull)
            if not p_text.strip("\n"):
                continue
            lines.append((question_level, p_text))
            level_set.add(question_level)
            for run in p.runs:
                if "lastRenderedPageBreak" in run._element.xml:
                    pn += 1
                    continue
                if "w:br" in run._element.xml and 'type="page"' in run._element.xml:
                    pn += 1

        sorted_levels = sorted(level_set)

        h2_level = sorted_levels[1] if len(sorted_levels) > 1 else 1
        h2_level = sorted_levels[-2] if h2_level == sorted_levels[-1] and len(sorted_levels) > 2 else h2_level

        root = Node(level=0, depth=h2_level, texts=[])
        root.build_tree(lines)

        return [element for element in root.get_tree() if element]