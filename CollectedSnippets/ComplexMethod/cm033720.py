def get_errors(self, paths: list[str]) -> list[SanityMessage]:
        """Return error messages related to issues with the file."""
        messages: list[SanityMessage] = []

        # unused errors

        unused: list[tuple[int, str, str]] = []

        if self.test.no_targets or self.test.all_targets:
            # tests which do not accept a target list, or which use all targets, always return all possible errors, so all ignores can be checked
            targets = SanityTargets.get_targets()
            test_targets = SanityTargets.filter_and_inject_targets(self.test, targets)
            paths = [target.path for target in test_targets]

        for path in paths:
            path_entry = self.ignore_entries.get(path)

            if not path_entry:
                continue

            unused.extend((line_no, path, code) for code, line_no in path_entry.items() if line_no not in self.used_line_numbers)

        messages.extend(SanityMessage(
            code=self.code,
            message="Ignoring '%s' on '%s' is unnecessary" % (code, path) if self.code else "Ignoring '%s' is unnecessary" % path,
            path=self.parser.relative_path,
            line=line,
            column=1,
            confidence=calculate_best_confidence(((self.parser.path, line), (path, 0)), self.args.metadata) if self.args.metadata.changes else None,
        ) for line, path, code in unused)

        return messages