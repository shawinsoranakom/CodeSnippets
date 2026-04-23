def wrapped(a, b):
        if JS_Undefined in (a, b):
            return _NaN
        # null, "" --> 0
        a, b = (float_or_none(
            (x.strip() if isinstance(x, compat_basestring) else x) or 0,
            default=_NaN) for x in (a, b))
        if _NaN in (a, b):
            return _NaN
        try:
            return op(a, b)
        except ZeroDivisionError:
            return _NaN if not (div and (a or b)) else _Infinity