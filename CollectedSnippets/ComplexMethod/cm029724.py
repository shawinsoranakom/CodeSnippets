def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    use_bytes = isinstance(cmd, bytes)

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    dirname, cmd = os.path.split(cmd)
    if dirname:
        path = [dirname]
    else:
        if path is None:
            path = os.environ.get("PATH", None)
            if path is None:
                try:
                    path = os.confstr("CS_PATH")
                except (AttributeError, ValueError):
                    # os.confstr() or CS_PATH is not available
                    path = os.defpath
            # bpo-35755: Don't use os.defpath if the PATH environment variable
            # is set to an empty string

        # PATH='' doesn't match, whereas PATH=':' looks in the current
        # directory
        if not path:
            return None

        if use_bytes:
            path = os.fsencode(path)
            path = path.split(os.fsencode(os.pathsep))
        else:
            path = os.fsdecode(path)
            path = path.split(os.pathsep)

        if sys.platform == "win32" and _win_path_needs_curdir(cmd, mode):
            curdir = os.curdir
            if use_bytes:
                curdir = os.fsencode(curdir)
            path.insert(0, curdir)

    if sys.platform == "win32":
        # PATHEXT is necessary to check on Windows.
        pathext_source = os.getenv("PATHEXT") or _WIN_DEFAULT_PATHEXT
        pathext = pathext_source.split(os.pathsep)
        pathext = [ext.rstrip('.') for ext in pathext if ext]

        if use_bytes:
            pathext = [os.fsencode(ext) for ext in pathext]

        files = [cmd + ext for ext in pathext]

        # If X_OK in mode, simulate the cmd.exe behavior: look at direct
        # match if and only if the extension is in PATHEXT.
        # If X_OK not in mode, simulate the first result of where.exe:
        # always look at direct match before a PATHEXT match.
        normcmd = cmd.upper()
        if not (mode & os.X_OK) or any(normcmd.endswith(ext.upper()) for ext in pathext):
            files.insert(0, cmd)
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None