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