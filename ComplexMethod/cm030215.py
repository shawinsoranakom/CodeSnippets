def _set_lines(self):
        if (
            self._lines is None
            and self.lineno is not None
            and self.end_lineno is not None
        ):
            lines = []
            for lineno in range(self.lineno, self.end_lineno + 1):
                # treat errors (empty string) and empty lines (newline) as the same
                line = linecache.getline(self.filename, lineno).rstrip()
                if not line and self._code is not None and self.filename.startswith("<"):
                    line = linecache._getline_from_code(self._code, lineno).rstrip()
                lines.append(line)
            self._lines = "\n".join(lines) + "\n"