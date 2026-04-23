def _display_window(self, pf: PythonFile, r: LintResult) -> Iterator[str]:
        """Display a window onto the code with an error"""
        if r.char is None or not self.report_column_numbers:
            yield f"{pf.path}:{r.line}: {r.name}"
        else:
            yield f"{pf.path}:{r.line}:{r.char + 1}: {r.name}"

        begin = max((r.line or 0) - ErrorLines.BEFORE, 1)
        end = min(begin + ErrorLines.WINDOW, 1 + len(pf.lines))

        for lineno in range(begin, end):
            source_line = pf.lines[lineno - 1].rstrip()
            yield f"{lineno:5} | {source_line}"
            if lineno == r.line:
                spaces = 8 + (r.char or 0)
                carets = len(source_line) if r.char is None else (r.length or 1)
                yield spaces * " " + carets * "^"