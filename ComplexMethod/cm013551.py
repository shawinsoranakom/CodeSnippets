def supercedes(a: object, b: object) -> bool:
    """``a`` is a more specific match than ``b``"""
    if isvar(b) and not isvar(a):
        return True
    s = unify(a, b)
    if s is False:
        return False
    s = {
        k: v
        for k, v in s.items()  # pyrefly: ignore[missing-attribute]
        if not isvar(k) or not isvar(v)
    }
    if reify(a, s) == a:
        return True
    if reify(b, s) == b:
        return False
    return False