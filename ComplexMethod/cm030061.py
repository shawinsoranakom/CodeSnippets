def mkdtemp(suffix=None, prefix=None, dir=None):
    """User-callable function to create and return a unique temporary
    directory.  The return value is the pathname of the directory.

    Arguments are as for mkstemp, except that the 'text' argument is
    not accepted.

    The directory is readable, writable, and searchable only by the
    creating user.

    Caller is responsible for deleting the directory when done with it.
    """

    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

    names = _get_candidate_names()
    if output_type is bytes:
        names = map(_os.fsencode, names)

    for seq in range(TMP_MAX):
        name = next(names)
        file = _os.path.join(dir, prefix + name + suffix)
        _sys.audit("tempfile.mkdtemp", file)
        try:
            _os.mkdir(file, 0o700)
        except FileExistsError:
            continue    # try again
        except PermissionError:
            # On Posix, this exception is raised when the user has no
            # write access to the parent directory.
            # On Windows, it is also raised when a directory with
            # the chosen name already exists, or if the parent directory
            # is not a directory.
            # We cannot distinguish between "directory-exists-error" and
            # "access-denied-error".
            if _os.name == 'nt' and _os.path.isdir(dir) and seq < TMP_MAX - 1:
                continue
            else:
                raise
        return _os.path.abspath(file)

    raise FileExistsError(_errno.EEXIST,
                          "No usable temporary directory name found")