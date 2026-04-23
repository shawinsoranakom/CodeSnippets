def expanduser(path):
    """Expand ~ and ~user constructions.  If user or $HOME is unknown,
    do nothing."""
    path = os.fspath(path)
    if isinstance(path, bytes):
        tilde = b'~'
    else:
        tilde = '~'
    if not path.startswith(tilde):
        return path
    sep = _get_sep(path)
    i = path.find(sep, 1)
    if i < 0:
        i = len(path)
    if i == 1:
        if 'HOME' not in os.environ:
            try:
                import pwd
            except ImportError:
                # pwd module unavailable, return path unchanged
                return path
            try:
                userhome = pwd.getpwuid(os.getuid()).pw_dir
            except KeyError:
                # bpo-10496: if the current user identifier doesn't exist in the
                # password database, return the path unchanged
                return path
        else:
            userhome = os.environ['HOME']
    else:
        try:
            import pwd
        except ImportError:
            # pwd module unavailable, return path unchanged
            return path
        name = path[1:i]
        if isinstance(name, bytes):
            name = os.fsdecode(name)
        try:
            pwent = pwd.getpwnam(name)
        except KeyError:
            # bpo-10496: if the user name from the path doesn't exist in the
            # password database, return the path unchanged
            return path
        userhome = pwent.pw_dir
    # if no user home, return the path unchanged on VxWorks
    if userhome is None and sys.platform == "vxworks":
        return path
    if isinstance(path, bytes):
        userhome = os.fsencode(userhome)
    userhome = userhome.rstrip(sep)
    return (userhome + path[i:]) or sep