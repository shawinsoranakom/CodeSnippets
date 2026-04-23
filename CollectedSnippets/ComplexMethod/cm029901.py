def updatecache(filename, module_globals=None):
    """Update a cache entry and return its list of lines.
    If something's wrong, print a message, discard the cache entry,
    and return an empty list."""

    # These imports are not at top level because linecache is in the critical
    # path of the interpreter startup and importing os and sys take a lot of time
    # and slows down the startup sequence.
    try:
        import os
        import sys
        import tokenize
    except ImportError:
        # These import can fail if the interpreter is shutting down
        return []

    entry = cache.pop(filename, None)
    if _source_unavailable(filename):
        return []

    if filename.startswith('<frozen '):
        # This is a frozen module, so we need to use the filename
        # from the module globals.
        if module_globals is None:
            return []

        fullname = module_globals.get('__file__')
        if fullname is None:
            return []
    else:
        fullname = filename
    try:
        stat = os.stat(fullname)
    except OSError:
        basename = filename

        # Realise a lazy loader based lookup if there is one
        # otherwise try to lookup right now.
        lazy_entry = entry if entry is not None and len(entry) == 1 else None
        if lazy_entry is None:
            lazy_entry = _make_lazycache_entry(filename, module_globals)
        if lazy_entry is not None:
            try:
                data = lazy_entry[0]()
            except (ImportError, OSError):
                pass
            else:
                if data is None:
                    # No luck, the PEP302 loader cannot find the source
                    # for this module.
                    return []
                entry = (
                    len(data),
                    None,
                    [line + '\n' for line in data.splitlines()],
                    fullname
                )
                cache[filename] = entry
                return entry[2]

        # Try looking through the module search path, which is only useful
        # when handling a relative filename.
        if os.path.isabs(filename):
            return []

        for dirname in sys.path:
            try:
                fullname = os.path.join(dirname, basename)
            except (TypeError, AttributeError):
                # Not sufficiently string-like to do anything useful with.
                continue
            try:
                stat = os.stat(fullname)
                break
            except (OSError, ValueError):
                pass
        else:
            return []
    except ValueError:  # may be raised by os.stat()
        return []
    try:
        with tokenize.open(fullname) as fp:
            lines = fp.readlines()
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    if not lines:
        lines = ['\n']
    elif not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    size, mtime = stat.st_size, stat.st_mtime
    cache[filename] = size, mtime, lines, fullname
    return lines