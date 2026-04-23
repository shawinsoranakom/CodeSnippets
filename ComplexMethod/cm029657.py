def commonpath(paths):
    """Given an iterable of path names, returns the longest common sub-path."""
    paths = tuple(map(os.fspath, paths))
    if not paths:
        raise ValueError('commonpath() arg is an empty iterable')

    if isinstance(paths[0], bytes):
        sep = b'\\'
        altsep = b'/'
        curdir = b'.'
    else:
        sep = '\\'
        altsep = '/'
        curdir = '.'

    try:
        drivesplits = [splitroot(p.replace(altsep, sep).lower()) for p in paths]
        split_paths = [p.split(sep) for d, r, p in drivesplits]

        # Check that all drive letters or UNC paths match. The check is made only
        # now otherwise type errors for mixing strings and bytes would not be
        # caught.
        if len({d for d, r, p in drivesplits}) != 1:
            raise ValueError("Paths don't have the same drive")

        drive, root, path = splitroot(paths[0].replace(altsep, sep))
        if len({r for d, r, p in drivesplits}) != 1:
            if drive:
                raise ValueError("Can't mix absolute and relative paths")
            else:
                raise ValueError("Can't mix rooted and not-rooted paths")

        common = path.split(sep)
        common = [c for c in common if c and c != curdir]

        split_paths = [[c for c in s if c and c != curdir] for s in split_paths]
        s1 = min(split_paths)
        s2 = max(split_paths)
        for i, c in enumerate(s1):
            if c != s2[i]:
                common = common[:i]
                break
        else:
            common = common[:len(s1)]

        return drive + root + sep.join(common)
    except (TypeError, AttributeError):
        genericpath._check_arg_types('commonpath', *paths)
        raise