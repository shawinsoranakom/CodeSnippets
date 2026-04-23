def detect_changes(args: TestConfig) -> t.Optional[list[str]]:
    """Return a list of changed paths."""
    if args.changed:
        paths = get_ci_provider().detect_changes(args)
    elif args.changed_from or args.changed_path:
        paths = args.changed_path or []
        if args.changed_from:
            paths += read_text_file(args.changed_from).splitlines()
    else:
        return None  # change detection not enabled

    if paths is None:
        return None  # act as though change detection not enabled, do not filter targets

    display.info('Detected changes in %d file(s).' % len(paths))

    for path in paths:
        display.info(path, verbosity=1)

    return paths