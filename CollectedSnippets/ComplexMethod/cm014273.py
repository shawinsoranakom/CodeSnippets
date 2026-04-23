def cmp_ne(a: object, b: object) -> bool:
    if isinstance(a, type):
        if type(a).__ne__ is type.__ne__:
            result = False if a is b else NotImplemented
        else:
            result = type(a).__ne__(a, b)
        if result is not NotImplemented:
            return result
    elif isinstance(type(a).__ne__, types.FunctionType):
        result = a.__ne__(b)
        if result is not NotImplemented:
            return result
        # Fall through to try b.__ne__(a) or cmp_eq
    if isinstance(b, type):
        if type(b).__ne__ is type.__ne__:
            result = False if a is b else NotImplemented
        else:
            result = type(b).__ne__(b, a)
        if result is not NotImplemented:
            return result
    elif isinstance(type(b).__ne__, types.FunctionType):
        result = b.__ne__(a)
        if result is not NotImplemented:
            return result
    return not cmp_eq(a, b)