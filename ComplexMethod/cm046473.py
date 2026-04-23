def windows_runtime_dirs_for_patterns(
    required_patterns: Iterable[str],
    candidate_dirs: Iterable[str] | None = None,
) -> list[str]:
    directories = (
        list(candidate_dirs) if candidate_dirs is not None else windows_runtime_dirs()
    )
    matching_dirs: list[str] = []
    for pattern in required_patterns:
        matched_dirs = [
            directory for directory in directories if any(Path(directory).glob(pattern))
        ]
        if not matched_dirs:
            return []
        for directory in matched_dirs:
            if directory not in matching_dirs:
                matching_dirs.append(directory)
    return matching_dirs