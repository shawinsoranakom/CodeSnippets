def is_ignored_path(path, ignore_patterns):
    """
    Check if the given path should be ignored or not based on matching
    one of the glob style `ignore_patterns`.
    """
    path = Path(path)

    def ignore(pattern):
        return fnmatch.fnmatchcase(path.name, pattern) or fnmatch.fnmatchcase(
            str(path), pattern
        )

    return any(ignore(pattern) for pattern in normalize_path_patterns(ignore_patterns))