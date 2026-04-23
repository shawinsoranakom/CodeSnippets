def pos_to_xy(self, pos: int) -> CursorXY:
        if not self.rows:
            return 0, 0

        remaining = pos
        for y, row in enumerate(self.rows):
            if remaining <= len(row.char_widths):
                # Prompt-only leading rows are terminal scenery, not real
                # buffer positions. Treating them as real just manufactures
                # bugs.
                if remaining == 0 and not row.char_widths and row.buffer_advance == 0 and y < len(self.rows) - 1:
                    continue
                x = row.prompt_width
                for width in row.char_widths[:remaining]:
                    x += width
                return x, y
            remaining -= row.buffer_advance
        last_row = self.rows[-1]
        return last_row.width - last_row.suffix_width, len(self.rows) - 1