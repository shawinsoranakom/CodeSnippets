def relpath(path, start=None):
    """Return a relative version of a path"""

    path = os.fspath(path)
    if not path:
        raise ValueError("no path specified")

    if isinstance(path, bytes):
        curdir = b'.'
        sep = b'/'
        pardir = b'..'
    else:
        curdir = '.'
        sep = '/'
        pardir = '..'

    if start is None:
        start = curdir
    else:
        start = os.fspath(start)

    try:
        start_tail = abspath(start).lstrip(sep)
        path_tail = abspath(path).lstrip(sep)
        start_list = start_tail.split(sep) if start_tail else []
        path_list = path_tail.split(sep) if path_tail else []
        # Work out how much of the filepath is shared by start and path.
        i = len(genericpath._commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return sep.join(rel_list)
    except (TypeError, AttributeError, BytesWarning, DeprecationWarning):
        genericpath._check_arg_types('relpath', path, start)
        raise