def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        target_paths = set(target.path for target in self.filter_remote_targets(list(targets.targets)))

        plugin_dir = os.path.join(SANITY_ROOT, 'pylint', 'plugins')
        plugin_names = sorted(p[0] for p in [
            os.path.splitext(p) for p in os.listdir(plugin_dir)] if p[1] == '.py' and p[0] != '__init__')

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        module_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in
                        paths if is_subdir(p, data_context().content.module_path)]
        module_dirs = sorted({p[0] for p in module_paths if len(p) > 1})

        large_module_group_threshold = 500
        large_module_groups = [key for key, value in
                               itertools.groupby(module_paths, lambda p: p[0] if len(p) > 1 else '') if len(list(value)) > large_module_group_threshold]

        large_module_group_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in paths
                                    if any(is_subdir(p, os.path.join(data_context().content.module_path, g)) for g in large_module_groups)]
        large_module_group_dirs = sorted({os.path.sep.join(p[:2]) for p in large_module_group_paths if len(p) > 2})

        contexts = []
        remaining_paths = set(paths)

        def add_context(available_paths: set[str], context_name: str, context_filter: c.Callable[[str], bool]) -> None:
            """Add the specified context to the context list, consuming available paths that match the given context filter."""
            filtered_paths = set(p for p in available_paths if context_filter(p))

            if selected_paths := sorted(path for path in filtered_paths if path in target_paths):
                contexts.append((context_name, True, selected_paths))

            if selected_paths := sorted(path for path in filtered_paths if path not in target_paths):
                contexts.append((context_name, False, selected_paths))

            available_paths -= filtered_paths

        def filter_path(path_filter: str = None) -> c.Callable[[str], bool]:
            """Return a function that filters out paths which are not a subdirectory of the given path."""

            def context_filter(path_to_filter: str) -> bool:
                """Return true if the given path matches, otherwise return False."""
                return is_subdir(path_to_filter, path_filter)

            return context_filter

        for large_module_dir in large_module_group_dirs:
            add_context(remaining_paths, 'modules/%s' % large_module_dir, filter_path(os.path.join(data_context().content.module_path, large_module_dir)))

        for module_dir in module_dirs:
            add_context(remaining_paths, 'modules/%s' % module_dir, filter_path(os.path.join(data_context().content.module_path, module_dir)))

        add_context(remaining_paths, 'modules', filter_path(data_context().content.module_path))
        add_context(remaining_paths, 'module_utils', filter_path(data_context().content.module_utils_path))

        add_context(remaining_paths, 'units', filter_path(data_context().content.unit_path))

        if data_context().content.collection:
            add_context(remaining_paths, 'collection', lambda p: True)
        else:
            add_context(remaining_paths, 'validate-modules', filter_path('test/lib/ansible_test/_util/controller/sanity/validate-modules/'))
            add_context(remaining_paths, 'validate-modules-unit', filter_path('test/lib/ansible_test/tests/validate-modules-unit/'))
            add_context(remaining_paths, 'code-smell', filter_path('test/lib/ansible_test/_util/controller/sanity/code-smell/'))
            add_context(remaining_paths, 'ansible-test-target', filter_path('test/lib/ansible_test/_util/target/'))
            add_context(remaining_paths, 'ansible-test', filter_path('test/lib/'))
            add_context(remaining_paths, 'test', filter_path('test/'))
            add_context(remaining_paths, 'hacking', filter_path('hacking/'))
            add_context(remaining_paths, 'ansible', lambda p: True)

        messages = []
        context_times = []

        collection_detail = None

        if data_context().content.collection:
            try:
                collection_detail = get_collection_detail(python)

                if not collection_detail.version:
                    display.warning('Skipping pylint collection version checks since no collection version was found.')
            except CollectionDetailError as ex:
                display.warning('Skipping pylint collection version checks since collection detail loading failed: %s' % ex.reason)

        test_start = datetime.datetime.now(tz=datetime.timezone.utc)

        for context, is_target, context_paths in sorted(contexts):
            if not context_paths:
                continue

            context_start = datetime.datetime.now(tz=datetime.timezone.utc)
            messages += self.pylint(args, context, is_target, context_paths, plugin_dir, plugin_names, python, collection_detail)
            context_end = datetime.datetime.now(tz=datetime.timezone.utc)

            context_times.append('%s: %d (%s)' % (context, len(context_paths), context_end - context_start))

        test_end = datetime.datetime.now(tz=datetime.timezone.utc)

        for context_time in context_times:
            display.info(context_time, verbosity=4)

        display.info('total: %d (%s)' % (len(paths), test_end - test_start), verbosity=4)

        errors = [SanityMessage(
            message=m['message'].replace('\n', ' '),
            path=m['path'],
            line=int(m['line']),
            column=int(m['column']),
            level=m['type'],
            code=m['symbol'],
        ) for m in messages]

        if args.explain:
            return SanitySuccess(self.name)

        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)