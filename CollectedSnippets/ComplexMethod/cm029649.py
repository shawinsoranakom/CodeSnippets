def _setoption(arg):
    parts = arg.split(':')
    if len(parts) > 5:
        raise _wm._OptionError("too many fields (max 5): %r" % (arg,))
    while len(parts) < 5:
        parts.append('')
    action, message, category, module, lineno = [s.strip()
                                                 for s in parts]
    action = _wm._getaction(action)
    category = _wm._getcategory(category)
    if message or module:
        import re
    if message:
        if len(message) >= 2 and message[0] == message[-1] == '/':
            message = message[1:-1]
        else:
            message = re.escape(message)
    if module:
        if len(module) >= 2 and module[0] == module[-1] == '/':
            module = module[1:-1]
        else:
            module = re.escape(module) + r'\z'
    if lineno:
        try:
            lineno = int(lineno)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError):
            raise _wm._OptionError("invalid lineno %r" % (lineno,)) from None
    else:
        lineno = 0
    try:
        _wm.filterwarnings(action, message, category, module, lineno)
    except re.PatternError if message or module else ():
        if message:
            try:
                re.compile(message)
            except re.PatternError:
                raise _wm._OptionError(f"invalid regular expression for "
                                       f"message: {message!r}") from None
        if module:
            try:
                re.compile(module)
            except re.PatternError:
                raise _wm._OptionError(f"invalid regular expression for "
                                       f"module: {module!r}") from None
        # Should never happen.
        raise