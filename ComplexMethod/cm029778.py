def ismount(path):
    """Test whether a path is a mount point"""
    try:
        s1 = os.lstat(path)
    except (OSError, ValueError):
        # It doesn't exist -- so not a mount point. :-)
        return False
    else:
        # A symlink can never be a mount point
        if stat.S_ISLNK(s1.st_mode):
            return False

    path = os.fspath(path)
    if isinstance(path, bytes):
        parent = join(path, b'..')
    else:
        parent = join(path, '..')
    try:
        s2 = os.lstat(parent)
    except OSError:
        parent = realpath(parent)
        try:
            s2 = os.lstat(parent)
        except OSError:
            return False

    # path/.. on a different device as path or the same i-node as path
    return s1.st_dev != s2.st_dev or s1.st_ino == s2.st_ino