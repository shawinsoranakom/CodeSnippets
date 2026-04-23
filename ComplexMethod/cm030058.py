def _infer_return_type(*args):
    """Look at the type of all args and divine their implied return type."""
    return_type = None
    for arg in args:
        if arg is None:
            continue

        if isinstance(arg, _os.PathLike):
            arg = _os.fspath(arg)

        if isinstance(arg, bytes):
            if return_type is str:
                raise TypeError("Can't mix bytes and non-bytes in "
                                "path components.")
            return_type = bytes
        else:
            if return_type is bytes:
                raise TypeError("Can't mix bytes and non-bytes in "
                                "path components.")
            return_type = str
    if return_type is None:
        if tempdir is None or isinstance(tempdir, str):
            return str  # tempfile APIs return a str by default.
        else:
            # we could check for bytes but it'll fail later on anyway
            return bytes
    return return_type