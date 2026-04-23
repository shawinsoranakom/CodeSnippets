def synchronized(obj, lock=None, ctx=None):
    assert not isinstance(obj, SynchronizedBase), 'object already synchronized'
    ctx = ctx or get_context()

    if isinstance(obj, ctypes._SimpleCData):
        return Synchronized(obj, lock, ctx)
    elif isinstance(obj, ctypes.Array):
        if obj._type_ is ctypes.c_char:
            return SynchronizedString(obj, lock, ctx)
        return SynchronizedArray(obj, lock, ctx)
    else:
        cls = type(obj)
        try:
            scls = class_cache[cls]
        except KeyError:
            names = [field[0] for field in cls._fields_]
            d = {name: make_property(name) for name in names}
            classname = 'Synchronized' + cls.__name__
            scls = class_cache[cls] = type(classname, (SynchronizedBase,), d)
        return scls(obj, lock, ctx)