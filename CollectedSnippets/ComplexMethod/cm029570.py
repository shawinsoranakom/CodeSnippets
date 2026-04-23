def _rglob(root, pattern, condition):
    dirs = [root]
    recurse = pattern[:3] in {"**/", "**\\"}
    if recurse:
        pattern = pattern[3:]

    while dirs:
        d = dirs.pop(0)
        if recurse:
            dirs.extend(
                filter(
                    condition, (type(root)(f2) for f2 in os.scandir(d) if f2.is_dir())
                )
            )
        yield from (
            (f.relative_to(root), f)
            for f in d.glob(pattern)
            if f.is_file() and condition(f)
        )