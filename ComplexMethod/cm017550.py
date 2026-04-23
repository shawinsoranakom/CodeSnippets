def get_files(storage, ignore_patterns=None, location=""):
    """
    Recursively walk the storage directories yielding the paths
    of all files that should be copied.
    """
    if ignore_patterns is None:
        ignore_patterns = []
    directories, files = storage.listdir(location)
    for fn in files:
        # Match only the basename.
        if matches_patterns(fn, ignore_patterns):
            continue
        if location:
            fn = os.path.join(location, fn)
            # Match the full file path.
            if matches_patterns(fn, ignore_patterns):
                continue
        yield fn
    for dir in directories:
        if matches_patterns(dir, ignore_patterns):
            continue
        if location:
            dir = os.path.join(location, dir)
        yield from get_files(storage, ignore_patterns, dir)