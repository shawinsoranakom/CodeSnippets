def append(self, line: str) -> None:
        """Append the given line."""
        if self._lines_remaining <= 0:
            raise Exception('Diff range overflow.')

        entry = self._next_line_number, line

        if line.startswith(' '):
            pass
        elif line.startswith(self.prefix):
            self.lines.append(entry)

            if not self._range_start:
                self._range_start = self._next_line_number
        else:
            raise Exception('Unexpected diff content prefix.')

        self.lines_and_context.append(entry)

        self._lines_remaining -= 1

        if self._range_start:
            if self.is_complete:
                range_end = self._next_line_number
            elif line.startswith(' '):
                range_end = self._next_line_number - 1
            else:
                range_end = 0

            if range_end:
                self.ranges.append((self._range_start, range_end))
                self._range_start = 0

        self._next_line_number += 1