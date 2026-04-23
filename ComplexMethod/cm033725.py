def test_script(self, args: SanityConfig, targets: SanityTargets, virtualenv_python: PythonConfig, python: PythonConfig) -> TestResult:
        """Run the sanity test and return the result."""
        cmd = [virtualenv_python.path, self.path]

        env = ansible_environment(args, color=False)

        env.update(
            PYTHONUTF8='1',  # force all code-smell sanity tests to run with Python UTF-8 Mode enabled
            ANSIBLE_TEST_TARGET_PYTHON_VERSION=python.version,
            ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS=','.join(CONTROLLER_PYTHON_VERSIONS),
            ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS=','.join(REMOTE_ONLY_PYTHON_VERSIONS),
            ANSIBLE_TEST_FIX_MODE=str(int(args.fix)),
        )

        if self.min_max_python_only:
            min_python, max_python = self.supported_python_versions

            env.update(ANSIBLE_TEST_MIN_PYTHON=min_python)
            env.update(ANSIBLE_TEST_MAX_PYTHON=max_python)

        pattern = None
        data = None

        settings = self.conditionally_load_processor(args, python.version)

        paths = [target.path for target in targets.include]

        if self.config:
            if self.output == 'path-line-column-message':
                pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'
            elif self.output == 'path-message':
                pattern = '^(?P<path>[^:]*): (?P<message>.*)$'
            elif self.output == 'path-line-column-code-message':
                pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[^:]*): (?P<message>.*)$'
            else:
                raise ApplicationError('Unsupported output type: %s' % self.output)

        if not self.no_targets:
            if self.split_targets:
                target_paths = set(target.path for target in self.filter_remote_targets(list(targets.targets)))
                controller_path_list = sorted(set(paths) - target_paths)
                target_path_list = sorted(set(paths) & target_paths)
                paths = controller_path_list + ['--'] + target_path_list

            data = '\n'.join(paths)

            if data:
                display.info(data, verbosity=4)

        try:
            stdout, stderr = intercept_python(args, virtualenv_python, cmd, data=data, env=env, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if args.explain:
            return SanitySuccess(self.name)

        if stdout and not stderr:
            if pattern:
                matches = parse_to_list_of_dict(pattern, stdout)

                messages = [SanityMessage(
                    message=m['message'],
                    path=m['path'],
                    line=int(m.get('line', 0)),
                    column=int(m.get('column', 0)),
                    code=m.get('code'),
                ) for m in matches]

                messages = settings.process_errors(messages, paths)

                if not messages:
                    return SanitySuccess(self.name)

                return SanityFailure(self.name, messages=messages)

        if stderr or status:
            summary = '%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
            return SanityFailure(self.name, summary=summary)

        messages = settings.process_errors([], paths)

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)