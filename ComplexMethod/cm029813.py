def copy(x):
    """Shallow copy operation on arbitrary Python objects.

    See the module's __doc__ string for more info.
    """

    cls = type(x)

    if cls in _copy_atomic_types:
        return x
    if cls in _copy_builtin_containers:
        return cls.copy(x)


    if issubclass(cls, type):
        # treat it as a regular class:
        return x

    copier = getattr(cls, "__copy__", None)
    if copier is not None:
        return copier(x)

    reductor = dispatch_table.get(cls)
    if reductor is not None:
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
                raise Error("un(shallow)copyable object of type %s" % cls)

    if isinstance(rv, str):
        return x
    return _reconstruct(x, None, *rv)