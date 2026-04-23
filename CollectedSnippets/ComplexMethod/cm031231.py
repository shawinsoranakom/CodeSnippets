def _parse_makefile(filename, vars=None, keep_unresolved=True):
    """Parse a Makefile-style file.

    A dictionary containing name/value pairs is returned.  If an
    optional dictionary is passed in as the second argument, it is
    used instead of a new dictionary.
    """
    import re

    if vars is None:
        vars = {}
    done = {}
    notdone = {}

    with open(filename, encoding=sys.getfilesystemencoding(),
              errors="surrogateescape") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('#') or line.strip() == '':
            continue
        m = re.match(_variable_rx, line)
        if m:
            n, v = m.group(1, 2)
            notdone[n] = v.strip()

    # Variables with a 'PY_' prefix in the makefile. These need to
    # be made available without that prefix through sysconfig.
    # Special care is needed to ensure that variable expansion works, even
    # if the expansion uses the name without a prefix.
    renamed_variables = ('CFLAGS', 'LDFLAGS', 'CPPFLAGS')

    def resolve_var(name):
        def repl(m):
            n = m[1]
            if n == '$':
                return '$'
            elif n == '':
                # bogus variable reference (e.g. "prefix=$/opt/python")
                if keep_unresolved:
                    return m[0]
                raise ValueError
            elif n[0] == '(' and n[-1] == ')':
                n = n[1:-1]
            elif n[0] == '{' and n[-1] == '}':
                n = n[1:-1]

            if n in done:
                return str(done[n])
            elif n in notdone:
                return str(resolve_var(n))
            elif n in os.environ:
                # do it like make: fall back to environment
                return os.environ[n]
            elif n in renamed_variables:
                if name.startswith('PY_') and name[3:] in renamed_variables:
                    return ""
                n = 'PY_' + n
                if n in notdone:
                    return str(resolve_var(n))
                else:
                    assert n not in done
                    return ""
            else:
                done[n] = ""
                return ""

        assert name not in done
        done[name] = ""
        try:
            value = re.sub(_findvar_rx, repl, notdone[name])
        except ValueError:
            del done[name]
            return ""
        value = value.strip()
        if name not in _ALWAYS_STR:
            try:
                value = int(value)
            except ValueError:
                pass
        done[name] = value
        if name.startswith('PY_') and name[3:] in renamed_variables:
            name = name[3:]
            if name not in done:
                done[name] = value
        return value

    for n in notdone:
        if n not in done:
            resolve_var(n)

    # strip spurious spaces
    for k, v in done.items():
        if isinstance(v, str):
            done[k] = v.strip()

    # save the results in the global dictionary
    vars.update(done)
    return vars