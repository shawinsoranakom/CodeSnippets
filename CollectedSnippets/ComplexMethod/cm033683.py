def integration_test_environment(
    args: IntegrationConfig,
    target: IntegrationTarget,
    inventory_path_src: str,
) -> c.Iterator[IntegrationEnvironment]:
    """Context manager that prepares the integration test environment and cleans it up."""
    ansible_config_src = args.get_ansible_config()
    ansible_config_relative = os.path.join(data_context().content.integration_path, '%s.cfg' % args.command)

    if args.no_temp_workdir or 'no/temp_workdir/' in target.aliases:
        display.warning('Disabling the temp work dir is a temporary debugging feature that may be removed in the future without notice.')

        integration_dir = os.path.join(data_context().content.root, data_context().content.integration_path)
        targets_dir = os.path.join(data_context().content.root, data_context().content.integration_targets_path)
        inventory_path = inventory_path_src
        ansible_config = ansible_config_src
        vars_file = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

        yield IntegrationEnvironment(data_context().content.root, integration_dir, targets_dir, inventory_path, ansible_config, vars_file)
        return

    # When testing a collection, the temporary directory must reside within the collection.
    # This is necessary to enable support for the default collection for non-collection content (playbooks and roles).
    root_temp_dir = os.path.join(ResultType.TMP.path, 'integration')

    prefix = '%s-' % target.name
    suffix = '-\u00c5\u00d1\u015a\u00cc\u03b2\u0141\u00c8'

    if args.no_temp_unicode or 'no/temp_unicode/' in target.aliases:
        display.warning('Disabling unicode in the temp work dir is a temporary debugging feature that may be removed in the future without notice.')
        suffix = '-ansible'

    if args.explain:
        temp_dir = os.path.join(root_temp_dir, '%stemp%s' % (prefix, suffix))
    else:
        make_dirs(root_temp_dir)
        temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=root_temp_dir)

    try:
        display.info('Preparing temporary directory: %s' % temp_dir, verbosity=2)

        inventory_relative_path = get_inventory_relative_path(args)
        inventory_path = os.path.join(temp_dir, inventory_relative_path)

        cache = IntegrationCache(args)

        target_dependencies = sorted([target] + list(cache.dependency_map.get(target.name, set())))

        files_needed = get_files_needed(target_dependencies)
        collection_roots = get_collection_roots_needed(target_dependencies)

        integration_dir = os.path.join(temp_dir, data_context().content.integration_path)
        targets_dir = os.path.join(temp_dir, data_context().content.integration_targets_path)
        ansible_config = os.path.join(temp_dir, ansible_config_relative)

        vars_file_src = os.path.join(data_context().content.root, data_context().content.integration_vars_path)
        vars_file = os.path.join(temp_dir, data_context().content.integration_vars_path)

        file_copies = [
            (ansible_config_src, ansible_config),
            (inventory_path_src, inventory_path),
        ]

        if os.path.exists(vars_file_src):
            file_copies.append((vars_file_src, vars_file))

        file_copies += [(path, os.path.join(temp_dir, path)) for path in files_needed]

        integration_targets_relative_path = data_context().content.integration_targets_path

        directory_copies = [
            (
                os.path.join(integration_targets_relative_path, target.relative_path),
                os.path.join(temp_dir, integration_targets_relative_path, target.relative_path),
            )
            for target in target_dependencies
        ]

        directory_copies = sorted(set(directory_copies))
        file_copies = sorted(set(file_copies))

        if not args.explain:
            make_dirs(integration_dir)

        for dir_src, dir_dst in directory_copies:
            display.info('Copying %s/ to %s/' % (dir_src, dir_dst), verbosity=2)

            if not args.explain:
                shutil.copytree(to_bytes(dir_src), to_bytes(dir_dst), symlinks=True)  # type: ignore[type-var,arg-type]  # type stub omits bytes path support

        for file_src, file_dst in file_copies:
            display.info('Copying %s to %s' % (file_src, file_dst), verbosity=2)

            if not args.explain:
                make_dirs(os.path.dirname(file_dst))
                shutil.copy2(file_src, file_dst)

        yield IntegrationEnvironment(temp_dir, integration_dir, targets_dir, inventory_path, ansible_config, vars_file, collection_roots)
    finally:
        if not args.explain:
            remove_tree(temp_dir)