def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        env = ansible_environment(args, color=False)
        env.update(get_powershell_injector_env(args.controller_powershell, env))

        settings = self.load_processor(args)

        target_per_type = collections.defaultdict(list)

        for target in targets.include:
            target_per_type[self.get_plugin_type(target)].append(target)

        # Remove plugins that cannot be associated to a single file (test and filter plugins).
        for plugin_type in MULTI_FILE_PLUGINS:
            target_per_type.pop(plugin_type, None)

        cmd = [
            python.path,
            os.path.join(SANITY_ROOT, 'validate-modules', 'validate.py'),
            '--format', 'json',
            '--arg-spec',
        ]  # fmt: skip

        if data_context().content.collection:
            cmd.extend(['--collection', data_context().content.collection.directory])

            try:
                collection_detail = get_collection_detail(python)

                if collection_detail.version:
                    cmd.extend(['--collection-version', collection_detail.version])
                else:
                    display.warning('Skipping validate-modules collection version checks since no collection version was found.')
            except CollectionDetailError as ex:
                display.warning('Skipping validate-modules collection version checks since collection detail loading failed: %s' % ex.reason)
        else:
            path = self.get_archive_path(args)

            if os.path.exists(path):
                temp_dir = process_scoped_temporary_directory(args)

                with tarfile.open(path) as file:
                    file.extractall(temp_dir, filter='data')

                cmd.extend([
                    '--original-plugins', temp_dir,
                ])

        errors = []

        for plugin_type, plugin_targets in sorted(target_per_type.items()):
            paths = [target.path for target in plugin_targets]
            plugin_cmd = list(cmd)

            if plugin_type != 'modules':
                plugin_cmd += ['--plugin-type', plugin_type]

            plugin_cmd += paths

            try:
                stdout, stderr = run_command(args, plugin_cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr or status not in (0, 3):
                raise SubprocessError(cmd=plugin_cmd, status=status, stderr=stderr, stdout=stdout)

            if args.explain:
                continue

            messages = json.loads(stdout)

            for filename in messages:
                output = messages[filename]

                for item in output['errors']:
                    errors.append(SanityMessage(
                        path=filename,
                        line=int(item['line']) if 'line' in item else 0,
                        column=int(item['column']) if 'column' in item else 0,
                        code='%s' % item['code'],
                        message=item['msg'],
                    ))

        all_paths = [target.path for target in targets.include]
        all_errors = settings.process_errors(errors, all_paths)

        if args.explain:
            return SanitySuccess(self.name)

        if all_errors:
            return SanityFailure(self.name, messages=all_errors)

        return SanitySuccess(self.name)