def _coerce_args(*args):
    # Invokes decode if necessary to create str args
    # and returns the coerced inputs along with
    # an appropriate result coercion function
    #   - noop for str inputs
    #   - encoding function otherwise
    str_input = None
    for arg in args:
        if arg:
            if str_input is None:
                str_input = isinstance(arg, str)
            else:
                if isinstance(arg, str) != str_input:
                    raise TypeError("Cannot mix str and non-str arguments")
    if str_input is None:
        for arg in args:
            if arg is not None:
                str_input = isinstance(arg, str)
                break
    if str_input is not False:
        return args + (_noop,)
    return _decode_args(args) + (_encode_result,)