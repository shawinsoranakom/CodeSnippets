def walk_integration_targets() -> c.Iterable[IntegrationTarget]:
    """Return an iterable of integration targets."""
    path = data_context().content.integration_targets_path
    modules = frozenset(target.module for target in walk_module_targets())
    paths = data_context().content.walk_files(path)
    prefixes = load_integration_prefixes()
    targets_path_tuple = tuple(path.split(os.path.sep))

    entry_dirs = (
        'defaults',
        'files',
        'handlers',
        'meta',
        'tasks',
        'templates',
        'vars',
    )

    entry_files = (
        'main.yml',
        'main.yaml',
    )

    entry_points = []

    for entry_dir in entry_dirs:
        for entry_file in entry_files:
            entry_points.append(os.path.join(os.path.sep, entry_dir, entry_file))

    # any directory with at least one file is a target
    path_tuples = set(tuple(os.path.dirname(p).split(os.path.sep))
                      for p in paths)

    # also detect targets which are ansible roles, looking for standard entry points
    path_tuples.update(tuple(os.path.dirname(os.path.dirname(p)).split(os.path.sep))
                       for p in paths if any(p.endswith(entry_point) for entry_point in entry_points))

    # remove the top-level directory if it was included
    if targets_path_tuple in path_tuples:
        path_tuples.remove(targets_path_tuple)

    previous_path_tuple = None
    paths = []

    for path_tuple in sorted(path_tuples):
        if previous_path_tuple and previous_path_tuple == path_tuple[:len(previous_path_tuple)]:
            # ignore nested directories
            continue

        previous_path_tuple = path_tuple
        paths.append(os.path.sep.join(path_tuple))

    for path in paths:
        yield IntegrationTarget(to_text(path), modules, prefixes)