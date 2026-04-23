def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str},
             tuple=tuple, type=type, len=len):
    """Make a cache key from optionally typed positional and keyword arguments

    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.

    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.

    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way is *much*
    # faster; however, it means that f(x=1, y=2) will now be treated as a
    # distinct call from f(y=2, x=1) which will be cached separately.
    key = args
    if kwds:
        key = list(key)
        key += kwd_mark
        for item in kwds.items():
            key += item
        key = tuple(key)
    if typed:
        key += tuple([type(v) for v in args])
        if kwds:
            key += tuple([type(v) for v in kwds.values()])
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return key