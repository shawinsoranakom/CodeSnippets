def _floor_ceil_helper(a: sympy.Basic, fn: Callable[..., sympy.Basic]) -> sympy.Basic:
    import sympy

    if isinstance(a, sympy.Mul):
        aa = a.args
        if len(aa) == 2 and isinstance(aa[0], sympy.Float) and aa[1].is_integer:
            coef = sympy.Integer(aa[0])
            if aa[0] == coef:  # structural equality test
                return coef * aa[1]
    if (
        isinstance(a, sympy.Float)
        and a == sympy.Integer(a)
        or isinstance(a, sympy.Integer)
    ):
        return sympy.Integer(a)
    return fn(a)