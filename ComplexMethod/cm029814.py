def deepcopy(x, memo=None):
    """Deep copy operation on arbitrary Python objects.

    See the module's __doc__ string for more info.
    """

    cls = type(x)

    if cls in _atomic_types:
        return x

    d = id(x)
    if memo is None:
        memo = {}
    else:
        y = memo.get(d, None)
        if y is not None:
            return y

    copier = _deepcopy_dispatch.get(cls)
    if copier is not None:
        y = copier(x, memo)
    else:
        if issubclass(cls, type):
            y = x # atomic copy
        else:
            copier = getattr(x, "__deepcopy__", None)
            if copier is not None:
                y = copier(memo)
            else:
                reductor = dispatch_table.get(cls)
                if reductor:
                    rv = reductor(x)
                else:
                    reductor = getattr(x, "__reduce_ex__", None)
                    if reductor is not None:
                        rv = reductor(4)
                    else:
                        reductor = getattr(x, "__reduce__", None)
                        if reductor:
                            rv = reductor()
                        else:
                            raise Error(
                                "un(deep)copyable object of type %s" % cls)
                if isinstance(rv, str):
                    y = x
                else:
                    y = _reconstruct(x, memo, *rv)

    # If is its own copy, don't memoize.
    if y is not x:
        memo[d] = y
        _keep_alive(x, memo) # Make sure x lives at least as long as d
    return y