def pylint(
        args: SanityConfig,
        context: str,
        is_target: bool,
        paths: list[str],
        plugin_dir: str,
        plugin_names: list[str],
        python: PythonConfig,
        collection_detail: CollectionDetail,
    ) -> list[dict[str, str]]:
        """Run pylint using the config specified by the context on the specified paths."""
        rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', context.split('/')[0] + '.cfg')

        if not os.path.exists(rcfile):
            if data_context().content.collection:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'collection.cfg')
            else:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'default.cfg')

        if is_target:
            context_label = 'target'
            min_python_version = REMOTE_ONLY_PYTHON_VERSIONS[0]
        else:
            context_label = 'controller'
            min_python_version = CONTROLLER_PYTHON_VERSIONS[0]

        load_plugins = set(plugin_names)
        plugin_options: dict[str, str] = {}

        # plugin: deprecated (ansible-test)
        if data_context().content.collection:
            plugin_options.update({'--collection-name': data_context().content.collection.full_name})
            plugin_options.update({'--collection-path': os.path.join(data_context().content.collection.root, data_context().content.collection.directory)})

            if collection_detail and collection_detail.version:
                plugin_options.update({'--collection-version': collection_detail.version})

        # plugin: pylint.extensions.mccabe
        if args.enable_optional_errors:
            load_plugins.add('pylint.extensions.mccabe')
            plugin_options.update({'--max-complexity': '20'})

        options = {
            '--py-version': min_python_version,
            '--load-plugins': ','.join(sorted(load_plugins)),
            '--rcfile': rcfile,
            '--jobs': '0',
            '--reports': 'n',
            '--output-format': 'json',
        }

        cmd = [python.path, '-m', 'pylint']
        cmd.extend(itertools.chain.from_iterable((options | plugin_options).items()))
        cmd.extend(paths)

        append_python_path = [plugin_dir]

        if data_context().content.collection:
            append_python_path.append(data_context().content.collection.root)

        env = ansible_environment(args)
        env['PYTHONPATH'] += os.path.pathsep + os.path.pathsep.join(append_python_path)

        # expose plugin paths for use in custom plugins
        env.update(dict(('ANSIBLE_TEST_%s_PATH' % k.upper(), os.path.abspath(v) + os.path.sep) for k, v in data_context().content.plugin_paths.items()))

        # Set PYLINTHOME to prevent pylint from checking for an obsolete directory, which can result in a test failure due to stderr output.
        # See: https://github.com/PyCQA/pylint/blob/e6c6bf5dfd61511d64779f54264b27a368c43100/pylint/constants.py#L148
        pylint_home = os.path.join(ResultType.TMP.path, 'pylint')
        make_dirs(pylint_home)
        env.update(PYLINTHOME=pylint_home)

        if paths:
            display.info(f'Checking {len(paths)} file(s) in context {context!r} ({context_label}) with config: {rcfile}', verbosity=1)

            try:
                stdout, stderr = run_command(args, cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr or status >= 32:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
        else:
            stdout = None

        if not args.explain and stdout:
            messages = json.loads(stdout)
        else:
            messages = []

        expected_paths = set(paths)

        unexpected_messages = [message for message in messages if message["path"] not in expected_paths]
        messages = [message for message in messages if message["path"] in expected_paths]

        for unexpected_message in unexpected_messages:
            display.info(f"Unexpected message: {json.dumps(unexpected_message)}", verbosity=4)

        if unexpected_messages:
            display.notice(f"Discarded {len(unexpected_messages)} unexpected messages. Use -vvvv to display.")

        return messages