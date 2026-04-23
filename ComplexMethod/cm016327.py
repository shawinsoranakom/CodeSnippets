def _lint_file(self, p: Path) -> bool:
        if self.args.verbose:
            print(p, "Reading", file=sys.stderr)

        pf = self.make_file(p)
        replacement, results = self._replace(pf)

        if display := list(self._display(pf, results)):
            print(*display, sep="\n")
        if results and self.args.fix and pf.path and pf.contents != replacement:
            pf.path.write_text(replacement)

        return not results or self.args.fix and all(r.is_edit for r in results)