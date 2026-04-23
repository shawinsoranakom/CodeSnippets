def get_argspec(ob):
    '''Return a string describing the signature of a callable object, or ''.

    For Python-coded functions and methods, the first line is introspected.
    Delete 'self' parameter for classes (.__init__) and bound methods.
    The next lines are the first lines of the doc string up to the first
    empty line or _MAX_LINES.    For builtins, this typically includes
    the arguments in addition to the return value.
    '''
    # Determine function object fob to inspect.
    try:
        ob_call = ob.__call__
    except BaseException:  # Buggy user object could raise anything.
        return ''  # No popup for non-callables.
    # For Get_argspecTest.test_buggy_getattr_class, CallA() & CallB().
    fob = ob_call if isinstance(ob_call, types.MethodType) else ob

    # Initialize argspec and wrap it to get lines.
    try:
        argspec = str(inspect.signature(fob))
    except Exception as err:
        msg = str(err)
        if msg.startswith(_invalid_method):
            return _invalid_method
        else:
            argspec = ''

    if isinstance(fob, type) and argspec == '()':
        # If fob has no argument, use default callable argspec.
        argspec = _default_callable_argspec

    lines = (textwrap.wrap(argspec, _MAX_COLS, subsequent_indent=_INDENT)
             if len(argspec) > _MAX_COLS else [argspec] if argspec else [])

    # Augment lines from docstring, if any, and join to get argspec.
    doc = inspect.getdoc(ob)
    if doc:
        for line in doc.split('\n', _MAX_LINES)[:_MAX_LINES]:
            line = line.strip()
            if not line:
                break
            if len(line) > _MAX_COLS:
                line = line[: _MAX_COLS - 3] + '...'
            lines.append(line)
    argspec = '\n'.join(lines)

    return argspec or _default_callable_argspec