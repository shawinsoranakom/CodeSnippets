def checkcache(filename=None):
    """Discard cache entries that are out of date.
    (This is not checked upon each call!)"""

    if filename is None:
        # get keys atomically
        filenames = cache.copy().keys()
    else:
        filenames = [filename]

    for filename in filenames:
        entry = cache.get(filename, None)
        if entry is None or len(entry) == 1:
            # lazy cache entry, leave it lazy.
            continue
        size, mtime, lines, fullname = entry
        if mtime is None:
            continue   # no-op for files loaded via a __loader__
        try:
            # This import can fail if the interpreter is shutting down
            import os
        except ImportError:
            return
        try:
            stat = os.stat(fullname)
        except (OSError, ValueError):
            cache.pop(filename, None)
            continue
        if size != stat.st_size or mtime != stat.st_mtime:
            cache.pop(filename, None)