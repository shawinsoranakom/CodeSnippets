def c2py(plural):
    """Gets a C expression as used in PO files for plural forms and returns a
    Python function that implements an equivalent expression.
    """

    if len(plural) > 1000:
        raise ValueError('plural form expression is too long')
    try:
        result, nexttok = _parse(_tokenize(plural))
        if nexttok:
            raise _error(nexttok)

        depth = 0
        for c in result:
            if c == '(':
                depth += 1
                if depth > 20:
                    # Python compiler limit is about 90.
                    # The most complex example has 2.
                    raise ValueError('plural form expression is too complex')
            elif c == ')':
                depth -= 1

        ns = {'_as_int': _as_int, '__name__': __name__}
        exec('''if True:
            def func(n):
                if not isinstance(n, int):
                    n = _as_int(n)
                return int(%s)
            ''' % result, ns)
        return ns['func']
    except RecursionError:
        # Recursion error can be raised in _parse() or exec().
        raise ValueError('plural form expression is too complex')