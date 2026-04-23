def wrapped(a, b):
        if JS_Undefined in (a, b):
            return False
        if isinstance(a, compat_basestring):
            b = compat_str(b or 0)
        elif isinstance(b, compat_basestring):
            a = compat_str(a or 0)
        return op(a or 0, b or 0)