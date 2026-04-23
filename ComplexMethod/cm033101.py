def _extract_text_block(self, start_pos):
        """Extract a text block (paragraphs, inline elements) until next block element"""
        end_pos = start_pos
        content_lines = [self.lines[start_pos]]

        i = start_pos + 1
        while i < len(self.lines):
            line = self.lines[i]
            # stop if we encounter a block element
            if re.match(r"^#{1,6}\s+.*$", line) or line.strip().startswith("```") or re.match(r"^\s*[-*+]\s+.*$", line) or re.match(r"^\s*\d+\.\s+.*$", line) or line.strip().startswith(">"):
                break
            elif not line.strip():
                # check if the next line is a block element
                if i + 1 < len(self.lines) and (
                    re.match(r"^#{1,6}\s+.*$", self.lines[i + 1])
                    or self.lines[i + 1].strip().startswith("```")
                    or re.match(r"^\s*[-*+]\s+.*$", self.lines[i + 1])
                    or re.match(r"^\s*\d+\.\s+.*$", self.lines[i + 1])
                    or self.lines[i + 1].strip().startswith(">")
                ):
                    break
                else:
                    content_lines.append(line)
                    end_pos = i
                    i += 1
            else:
                content_lines.append(line)
                end_pos = i
                i += 1

        return {
            "type": "text_block",
            "content": "\n".join(content_lines),
            "start_line": start_pos,
            "end_line": end_pos,
        }