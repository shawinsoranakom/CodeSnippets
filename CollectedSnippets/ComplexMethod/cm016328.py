def _replace(self, pf: PythonFile) -> tuple[str, list[LintResult]]:
        # Because of recursive replacements, we need to repeat replacing and reparsing
        # from the inside out until all possible replacements are complete
        previous_result_count = float("inf")
        first_results: list[LintResult] = []
        original = replacement = pf.contents
        results: list[LintResult] = []

        while True:
            try:
                results = sorted(self._lint(pf), key=LintResult.sort_key)
            except IndentationError as e:
                error, (_name, lineno, column, _line) = e.args

                results = [LintResult(error, lineno, column)]
                self._error(pf, *results)

            except ParseError as e:
                results = [LintResult(str(e), *e.token.start)]
                self._error(pf, *results)

            for i, ri in enumerate(results):
                if not ri.is_recursive:
                    for rj in results[i + 1 :]:
                        if ri.contains(rj):
                            rj.is_recursive = True
                        else:
                            break

            first_results = first_results or results
            if not results or len(results) >= previous_result_count:
                break
            previous_result_count = len(results)

            lines = pf.lines[:]
            for r in reversed(results):
                r.apply(lines)
            replacement = "".join(lines)

            if not any(r.is_recursive for r in results):
                break
            pf = pf.with_contents(replacement)

        if first_results and self.args.lintrunner:
            name = f"Suggested fixes for {self.linter_name}"
            msg = LintResult(name=name, original=original, replacement=replacement)
            first_results.append(msg)

        return replacement, first_results