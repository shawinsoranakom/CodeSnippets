def get_all_lines(self):
        """Get all display content as a list of lines (for testing)."""
        if not self.buffer:
            return []

        max_line = max(pos[0] for pos in self.buffer.keys())
        lines = []
        for line_num in range(max_line + 1):
            line_parts = []
            for col in range(self.width):
                if (line_num, col) in self.buffer:
                    text, _ = self.buffer[(line_num, col)]
                    line_parts.append((col, text))

            # Reconstruct line from parts
            if line_parts:
                line_parts.sort(key=lambda x: x[0])
                line = ""
                last_col = 0
                for col, text in line_parts:
                    if col > last_col:
                        line += " " * (col - last_col)
                    line += text
                    last_col = col + len(text)
                lines.append(line.rstrip())
            else:
                lines.append("")

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return lines