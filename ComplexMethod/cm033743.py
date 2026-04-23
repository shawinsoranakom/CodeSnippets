def detect_changes(self, args: TestConfig) -> t.Optional[list[str]]:
        """Initialize change detection."""
        result = LocalChanges(args)

        display.info('Detected branch %s forked from %s at commit %s' % (
            result.current_branch, result.fork_branch, result.fork_point))

        if result.untracked and not args.untracked:
            display.warning('Ignored %s untracked file(s). Use --untracked to include them.' %
                            len(result.untracked))

        if result.committed and not args.committed:
            display.warning('Ignored %s committed change(s). Omit --ignore-committed to include them.' %
                            len(result.committed))

        if result.staged and not args.staged:
            display.warning('Ignored %s staged change(s). Omit --ignore-staged to include them.' %
                            len(result.staged))

        if result.unstaged and not args.unstaged:
            display.warning('Ignored %s unstaged change(s). Omit --ignore-unstaged to include them.' %
                            len(result.unstaged))

        names = set()

        if args.tracked:
            names |= set(result.tracked)
        if args.untracked:
            names |= set(result.untracked)
        if args.committed:
            names |= set(result.committed)
        if args.staged:
            names |= set(result.staged)
        if args.unstaged:
            names |= set(result.unstaged)

        if not args.metadata.changes:
            args.metadata.populate_changes(result.diff)

            for path in result.untracked:
                if is_binary_file(path):
                    args.metadata.changes[path] = ((0, 0),)
                    continue

                line_count = len(read_text_file(path).splitlines())

                args.metadata.changes[path] = ((1, line_count),)

        return sorted(names)