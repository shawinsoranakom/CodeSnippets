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