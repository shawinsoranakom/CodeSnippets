def wrapped(a, b):
        if JS_Undefined in (a, b):
            return False
        if isinstance(a, str) or isinstance(b, str):
            return op(str(a or 0), str(b or 0))
        return op(a or 0, b or 0)