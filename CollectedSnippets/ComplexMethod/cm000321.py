def find_common_prefix(paths: list[str]) -> str:
    """Find the common directory prefix of a list of file paths."""
    if not paths:
        return ""
    if len(paths) == 1:
        parts = paths[0].rsplit('/', 1)
        return parts[0] + '/' if len(parts) > 1 else ""

    split_paths = [p.split('/') for p in paths]
    common = []
    for parts in zip(*split_paths):
        if len(set(parts)) == 1:
            common.append(parts[0])
        else:
            break

    return '/'.join(common) + '/' if common else ""