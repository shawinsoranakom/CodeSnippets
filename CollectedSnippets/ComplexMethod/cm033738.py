def test(self, args: SanityConfig, targets: SanityTargets) -> TestResult:
        exclude_file = os.path.join(SANITY_ROOT, 'shellcheck', 'exclude.txt')
        exclude = set(read_lines_without_comments(exclude_file, remove_blank_lines=True, optional=True))

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        if not find_executable('shellcheck', required='warning'):
            return SanitySkipped(self.name)

        cmd = [
            'shellcheck',
            '-e', ','.join(sorted(exclude)),
            '--format', 'checkstyle',
        ] + paths  # fmt: skip

        try:
            stdout, stderr = run_command(args, cmd, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr or status > 1:
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        # json output is missing file paths in older versions of shellcheck, so we'll use xml instead
        root: Element = fromstring(stdout)

        results = []

        for item in root:
            for entry in item:
                results.append(SanityMessage(
                    message=entry.attrib['message'],
                    path=item.attrib['name'],
                    line=int(entry.attrib['line']),
                    column=int(entry.attrib['column']),
                    level=entry.attrib['severity'],
                    code=entry.attrib['source'].replace('ShellCheck.', ''),
                ))

        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)