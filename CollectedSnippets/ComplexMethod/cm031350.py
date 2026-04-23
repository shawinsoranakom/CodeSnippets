def xy_to_pos(self, x: int, y: int) -> int:
        if not self.rows:
            return 0

        pos = 0
        for row in self.rows[:y]:
            pos += row.buffer_advance

        row = self.rows[y]
        cur_x = row.prompt_width
        char_widths = row.char_widths
        i = 0
        for i, width in enumerate(char_widths):
            if cur_x >= x:
                # Include trailing zero-width (combining) chars at this position
                for trailing_width in char_widths[i:]:
                    if trailing_width == 0:
                        pos += 1
                    else:
                        break
                return pos
            if width == 0:
                pos += 1
                continue
            cur_x += width
            pos += 1
        return pos