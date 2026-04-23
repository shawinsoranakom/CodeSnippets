def _get_default_tempdir(dirlist=None):
    """Calculate the default directory to use for temporary files.
    This routine should be called exactly once.

    We determine whether or not a candidate temp dir is usable by
    trying to create and write to a file in that directory.  If this
    is successful, the test file is deleted.  To prevent denial of
    service, the name of the test file must be randomized."""

    namer = _RandomNameSequence()
    if dirlist is None:
        dirlist = _candidate_tempdir_list()

    for dir in dirlist:
        if dir != _os.curdir:
            dir = _os.path.abspath(dir)
        for seq in range(TMP_MAX):
            name = next(namer)
            filename = _os.path.join(dir, name)
            try:
                fd = _os.open(filename, _bin_openflags, 0o600)
                try:
                    try:
                        _os.write(fd, b'blat')
                    finally:
                        _os.close(fd)
                finally:
                    _os.unlink(filename)
                return dir
            except FileExistsError:
                pass
            except PermissionError:
                # See the comment in mkdtemp().
                if _os.name == 'nt' and _os.path.isdir(dir):
                    continue
                break   # no point trying more names in this directory
            except OSError:
                break   # no point trying more names in this directory
    raise FileNotFoundError(_errno.ENOENT,
                            "No usable temporary directory found in %s" %
                            dirlist)