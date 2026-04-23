def expandvars(path):
    """Expand shell variables of the forms $var, ${var} and %var%.

    Unknown variables are left unchanged."""
    path = os.fspath(path)
    global _varsub, _varsubb
    if isinstance(path, bytes):
        if b'$' not in path and b'%' not in path:
            return path
        if not _varsubb:
            import re
            _varsubb = re.compile(_varpattern.encode(), re.ASCII).sub
        sub = _varsubb
        percent = b'%'
        brace = b'{'
        rbrace = b'}'
        dollar = b'$'
        environ = getattr(os, 'environb', None)
    else:
        if '$' not in path and '%' not in path:
            return path
        if not _varsub:
            import re
            _varsub = re.compile(_varpattern, re.ASCII).sub
        sub = _varsub
        percent = '%'
        brace = '{'
        rbrace = '}'
        dollar = '$'
        environ = os.environ

    def repl(m):
        lastindex = m.lastindex
        if lastindex is None:
            return m[0]
        name = m[lastindex]
        if lastindex == 1:
            if name == percent:
                return name
            if not name.endswith(percent):
                return m[0]
            name = name[:-1]
        else:
            if name == dollar:
                return name
            if name.startswith(brace):
                if not name.endswith(rbrace):
                    return m[0]
                name = name[1:-1]

        try:
            if environ is None:
                return os.fsencode(os.environ[os.fsdecode(name)])
            else:
                return environ[name]
        except KeyError:
            return m[0]

    return sub(repl, path)