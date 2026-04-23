def supercedes(a: tuple[type, ...], b: tuple[type, ...]) -> bool:
    """A is consistent and strictly more specific than B"""
    if len(a) < len(b):
        # only case is if a is empty and b is variadic
        return not a and len(b) == 1 and isvariadic(b[-1])
    elif len(a) == len(b):
        return all(map(issubclass, a, b))
    else:
        # len(a) > len(b)
        p1 = 0
        p2 = 0
        while p1 < len(a) and p2 < len(b):
            cur_a = a[p1]
            cur_b = b[p2]
            if not (isvariadic(cur_a) or isvariadic(cur_b)):
                if not issubclass(cur_a, cur_b):
                    return False
                p1 += 1
                p2 += 1
            elif isvariadic(cur_a):
                if p1 != len(a) - 1:
                    raise AssertionError(
                        f"Expected p1={p1} to equal len(a)-1={len(a) - 1}"
                    )
                return p2 == len(b) - 1 and issubclass(cur_a, cur_b)
            elif isvariadic(cur_b):
                if p2 != len(b) - 1:
                    raise AssertionError(
                        f"Expected p2={p2} to equal len(b)-1={len(b) - 1}"
                    )
                if not issubclass(cur_a, cur_b):
                    return False
                p1 += 1
        return p2 == len(b) - 1 and p1 == len(a)