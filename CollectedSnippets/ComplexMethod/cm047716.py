def which_files(file, mode=F_OK | X_OK, path=None, pathext=None):
    """ Locate a file in a path supplied as a part of the file name,
        or the user's path, or a supplied path.
        The function yields full paths (not necessarily absolute paths),
        in which the given file name matches an existing file in a directory on the path.

        >>> def test_which(expected, *args, **argd):
        ...     result = list(which_files(*args, **argd))
        ...     assert all(path in result for path in expected) if expected else not result, 'which_files: %s != %s' % (result, expected)
        ...
        ...     try:
        ...         result = which(*args, **argd)
        ...         path = expected[0]
        ...         assert split(result)[1] == split(expected[0])[1], 'which: %s not same binary %s' % (result, expected)
        ...     except IOError:
        ...         result = None
        ...         assert not expected, 'which: expecting %s' % expected

        >>> if windows: cmd = environ['COMSPEC']
        >>> if windows: test_which([cmd], 'cmd')
        >>> if windows: test_which([cmd], 'cmd.exe')
        >>> if windows: test_which([cmd], 'cmd', path=dirname(cmd))
        >>> if windows: test_which([cmd], 'cmd', pathext='.exe')
        >>> if windows: test_which([cmd], cmd)
        >>> if windows: test_which([cmd], cmd, path='<nonexistent>')
        >>> if windows: test_which([cmd], cmd, pathext='<nonexistent>')
        >>> if windows: test_which([cmd], cmd[:-4])
        >>> if windows: test_which([cmd], cmd[:-4], path='<nonexistent>')

        >>> if windows: test_which([], 'cmd', path='<nonexistent>')
        >>> if windows: test_which([], 'cmd', pathext='<nonexistent>')
        >>> if windows: test_which([], '<nonexistent>/cmd')
        >>> if windows: test_which([], cmd[:-4], pathext='<nonexistent>')

        >>> if not windows: sh = '/bin/sh'
        >>> if not windows: test_which([sh], 'sh')
        >>> if not windows: test_which([sh], 'sh', path=dirname(sh))
        >>> if not windows: test_which([sh], 'sh', pathext='<nonexistent>')
        >>> if not windows: test_which([sh], sh)
        >>> if not windows: test_which([sh], sh, path='<nonexistent>')
        >>> if not windows: test_which([sh], sh, pathext='<nonexistent>')

        >>> if not windows: test_which([], 'sh', mode=W_OK)  # not running as root, are you?
        >>> if not windows: test_which([], 'sh', path='<nonexistent>')
        >>> if not windows: test_which([], '<nonexistent>/sh')
    """
    filepath, file = split(file)

    if filepath:
        path = (filepath,)
    elif path is None:
        path = defpath
    elif isinstance(path, str):
        path = path.split(pathsep)

    if pathext is None:
        pathext = defpathext
    elif isinstance(pathext, str):
        pathext = pathext.split(pathsep)

    if not '' in pathext:
        pathext.insert(0, '') # always check command without extension, even for custom pathext

    for dir in path:
        basepath = join(dir, file)
        for ext in pathext:
            fullpath = basepath + ext
            if exists(fullpath) and access(fullpath, mode):
                yield fullpath