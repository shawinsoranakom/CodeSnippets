def cmp_eq(a: object, b: object) -> bool:
    # Note that the commented `is` check should ideally be removed. This is a
    # CPython optimization that skips the __eq__ checks it the obj id's are
    # same. But, these lines adds many `is` nodes in the Fx graph for
    # SymNodeVariable. For now, we can just skip this check. This is STILL
    # correct because one of the __eq__ checks will pass later, just could be
    # slow in some corner cases.
    # if a is b:
    #     return True
    if isinstance(a, type):
        # Default metaclass equality is identity-based. Preserve the reflected
        # operand fallback without tracing through type.__eq__.
        if type(a).__eq__ is type.__eq__:
            result = True if a is b else NotImplemented
        else:
            result = type(a).__eq__(a, b)
    else:
        result = a.__eq__(b)
    if result is NotImplemented:
        if isinstance(b, type):
            if type(b).__eq__ is type.__eq__:
                result = True if a is b else NotImplemented
            else:
                result = type(b).__eq__(b, a)
        else:
            result = b.__eq__(a)
    return result is not NotImplemented and result