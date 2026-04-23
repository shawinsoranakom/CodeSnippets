def _is_bad_block(self, b: _linter.Block, pf: _linter.PythonFile) -> bool:
        max_lines = self._max_lines[b.category]
        return (
            not (b.is_override or pf.omitted(pf.tokens, b.begin, b.end + 1))
            and b.line_count > max_lines
            and len(b.docstring) < self.args.min_docstring
            and (self.args.lint_local or not b.is_local)
            and (self.args.lint_protected or not b.name.startswith("_"))
        )