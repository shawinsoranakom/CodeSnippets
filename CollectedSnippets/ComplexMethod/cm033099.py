def extract_elements(self, delimiter=None, include_meta=False):
        """Extract individual elements (headers, code blocks, lists, etc.)"""
        sections = []

        i = 0
        dels = ""
        if delimiter:
            dels = self.get_delimiters(delimiter)
        if len(dels) > 0:
            text = "\n".join(self.lines)
            if include_meta:
                pattern = re.compile(dels)
                last_end = 0
                for m in pattern.finditer(text):
                    part = text[last_end : m.start()]
                    if part and part.strip():
                        sections.append(
                            {
                                "content": part.strip(),
                                "start_line": text.count("\n", 0, last_end),
                                "end_line": text.count("\n", 0, m.start()),
                            }
                        )
                    last_end = m.end()

                part = text[last_end:]
                if part and part.strip():
                    sections.append(
                        {
                            "content": part.strip(),
                            "start_line": text.count("\n", 0, last_end),
                            "end_line": text.count("\n", 0, len(text)),
                        }
                    )
            else:
                parts = re.split(dels, text)
                sections = [p.strip() for p in parts if p and p.strip()]
            return sections
        while i < len(self.lines):
            line = self.lines[i]

            if re.match(r"^#{1,6}\s+.*$", line):
                # header
                element = self._extract_header(i)
                sections.append(element if include_meta else element["content"])
                i = element["end_line"] + 1
            elif line.strip().startswith("```"):
                # code block
                element = self._extract_code_block(i)
                sections.append(element if include_meta else element["content"])
                i = element["end_line"] + 1
            elif re.match(r"^\s*[-*+]\s+.*$", line) or re.match(r"^\s*\d+\.\s+.*$", line):
                # list block
                element = self._extract_list_block(i)
                sections.append(element if include_meta else element["content"])
                i = element["end_line"] + 1
            elif line.strip().startswith(">"):
                # blockquote
                element = self._extract_blockquote(i)
                sections.append(element if include_meta else element["content"])
                i = element["end_line"] + 1
            elif line.strip():
                # text block (paragraphs and inline elements until next block element)
                element = self._extract_text_block(i)
                sections.append(element if include_meta else element["content"])
                i = element["end_line"] + 1
            else:
                i += 1

        if include_meta:
            sections = [section for section in sections if section["content"].strip()]
        else:
            sections = [section for section in sections if section.strip()]
        return sections