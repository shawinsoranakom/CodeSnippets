def test(self, args: SanityConfig, targets: SanityTargets) -> TestResult:
        env = common_environment()
        env.update(get_powershell_injector_env(args.controller_powershell, env))

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        if not find_executable('pwsh', required='warning', path=env.get('PATH')):
            return SanitySkipped(self.name)

        cmds = []

        if args.controller.is_managed or args.requirements:
            cmds.append(['pwsh', os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'sanity.pslint.ps1')])

        cmds.append(['pwsh', os.path.join(SANITY_ROOT, 'pslint', 'pslint.ps1')] + paths)

        stdout = ''

        for cmd in cmds:
            try:
                stdout, stderr = run_command(args, cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        severity = [
            'Information',
            'Warning',
            'Error',
            'ParseError',
        ]

        cwd = data_context().content.root + '/'

        # replace unicode smart quotes and ellipsis with ascii versions
        stdout = re.sub('[\u2018\u2019]', "'", stdout)
        stdout = re.sub('[\u201c\u201d]', '"', stdout)
        stdout = re.sub('[\u2026]', '...', stdout)

        messages = json.loads(stdout)

        errors = [SanityMessage(
            code=m['RuleName'],
            message=m['Message'],
            path=m['ScriptPath'].replace(cwd, ''),
            line=m['Line'] or 0,
            column=m['Column'] or 0,
            level=severity[m['Severity']],
        ) for m in messages]

        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)