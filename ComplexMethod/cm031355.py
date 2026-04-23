def _build_source_lines(
        self,
        offset: int,
        first_lineno: int,
    ) -> tuple[SourceLine, ...]:
        if offset == len(self.buffer) and (offset > 0 or first_lineno > 0):
            return ()

        pos = self.pos - offset
        lines = "".join(self.buffer[offset:]).split("\n")
        cursor_found = False
        lines_beyond_cursor = 0
        source_lines: list[SourceLine] = []
        current_offset = offset

        for line_index, line in enumerate(lines):
            lineno = first_lineno + line_index
            has_newline = line_index < len(lines) - 1
            line_len = len(line)
            cursor_index: int | None = None
            if 0 <= pos <= line_len:
                cursor_index = pos
                self.lxy = pos, lineno
                cursor_found = True
            elif cursor_found:
                lines_beyond_cursor += 1
                if lines_beyond_cursor > self.console.height:
                    break

            source_lines.append(
                SourceLine(
                    lineno=lineno,
                    text=line,
                    start_offset=current_offset,
                    has_newline=has_newline,
                    cursor_index=cursor_index,
                )
            )
            pos -= line_len + 1
            current_offset += line_len + (1 if has_newline else 0)

        return tuple(source_lines)