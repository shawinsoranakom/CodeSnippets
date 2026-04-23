def iter_builtin_types():
    # First try the explicit route.
    try:
        import _testinternalcapi
    except ImportError:
        _testinternalcapi = None
    if _testinternalcapi is not None:
        yield from _testinternalcapi.get_static_builtin_types()
        return

    # Fall back to making a best-effort guess.
    if hasattr(object, '__flags__'):
        # Look for any type object with the Py_TPFLAGS_STATIC_BUILTIN flag set.
        import datetime  # noqa: F401
        seen = set()
        for cls, subs in walk_class_hierarchy(object):
            if cls in seen:
                continue
            seen.add(cls)
            if not (cls.__flags__ & _TPFLAGS_STATIC_BUILTIN):
                # Do not walk its subclasses.
                subs[:] = []
                continue
            yield cls
    else:
        # Fall back to a naive approach.
        seen = set()
        for obj in __builtins__.values():
            if not isinstance(obj, type):
                continue
            cls = obj
            # XXX?
            if cls.__module__ != 'builtins':
                continue
            if cls == ExceptionGroup:
                # It's a heap type.
                continue
            if cls in seen:
                continue
            seen.add(cls)
            yield cls