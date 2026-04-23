def is_namedtuple(x: object) -> TypeGuard[NamedTuple]:
    t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple:
        return False
    f = getattr(t, "_fields", None)
    if not isinstance(f, tuple):
        return False
    return all(type(n).__name__ == "str" for n in f)