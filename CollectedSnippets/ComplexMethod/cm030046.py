def _iglob(pathname, root_dir, dir_fd, recursive, dironly,
           include_hidden=False):
    dirname, basename = os.path.split(pathname)
    if not has_magic(pathname):
        assert not dironly
        if basename:
            if _lexists(_join(root_dir, pathname), dir_fd):
                yield pathname
        else:
            # Patterns ending with a slash should match only directories
            if _isdir(_join(root_dir, dirname), dir_fd):
                yield pathname
        return
    if not dirname:
        if recursive and _isrecursive(basename):
            yield from _glob2(root_dir, basename, dir_fd, dironly,
                             include_hidden=include_hidden)
        else:
            yield from _glob1(root_dir, basename, dir_fd, dironly,
                              include_hidden=include_hidden)
        return
    # `os.path.split()` returns the argument itself as a dirname if it is a
    # drive or UNC path.  Prevent an infinite recursion if a drive or UNC path
    # contains magic characters (i.e. r'\\?\C:').
    if dirname != pathname and has_magic(dirname):
        dirs = _iglob(dirname, root_dir, dir_fd, recursive, True,
                      include_hidden=include_hidden)
    else:
        dirs = [dirname]
    if has_magic(basename):
        if recursive and _isrecursive(basename):
            glob_in_dir = _glob2
        else:
            glob_in_dir = _glob1
    else:
        glob_in_dir = _glob0
    for dirname in dirs:
        for name in glob_in_dir(_join(root_dir, dirname), basename, dir_fd, dironly,
                               include_hidden=include_hidden):
            yield os.path.join(dirname, name)