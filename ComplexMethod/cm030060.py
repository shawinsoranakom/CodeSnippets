def _mkstemp_inner(dir, pre, suf, flags, output_type):
    """Code common to mkstemp, TemporaryFile, and NamedTemporaryFile."""

    dir = _os.path.abspath(dir)
    names = _get_candidate_names()
    if output_type is bytes:
        names = map(_os.fsencode, names)

    for seq in range(TMP_MAX):
        name = next(names)
        file = _os.path.join(dir, pre + name + suf)
        _sys.audit("tempfile.mkstemp", file)
        try:
            fd = _os.open(file, flags, 0o600)
        except FileExistsError:
            continue    # try again
        except PermissionError:
            # See the comment in mkdtemp().
            if _os.name == 'nt' and _os.path.isdir(dir) and seq < TMP_MAX - 1:
                continue
            else:
                raise
        return fd, file

    raise FileExistsError(_errno.EEXIST,
                          "No usable temporary file name found")