def call_func_complex(op, /, value=None, *args, exc=None, **kwargs):
    if exc is not None:
        raise exc
    if op == '':
        raise ValueError('missing op')
    elif op == 'ident':
        if args or kwargs:
            raise Exception((args, kwargs))
        return value
    elif op == 'full-ident':
        return (value, args, kwargs)
    elif op == 'globals':
        if value is not None or args or kwargs:
            raise Exception((value, args, kwargs))
        return __name__
    elif op == 'interpid':
        if value is not None or args or kwargs:
            raise Exception((value, args, kwargs))
        return interpreters.get_current().id
    elif op == 'closure':
        if args or kwargs:
            raise Exception((args, kwargs))
        return get_call_func_closure(value)
    elif op == 'custom':
        if args or kwargs:
            raise Exception((args, kwargs))
        return Spam(value)
    elif op == 'custom-inner':
        if args or kwargs:
            raise Exception((args, kwargs))
        class Eggs(Spam):
            pass
        return Eggs(value)
    elif not isinstance(op, str):
        raise TypeError(op)
    else:
        raise NotImplementedError(op)