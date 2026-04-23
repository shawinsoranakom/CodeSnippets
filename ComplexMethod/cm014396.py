def simple_sympify(e):
    if isinstance(e, bool):
        return sympy.true if e else sympy.false
    elif isinstance(e, int):
        return sympy.Integer(e)
    elif isinstance(e, float):
        # infinity is special; we use it to bracket integers as well
        if math.isinf(e):
            return sympy.oo if e > 0 else -sympy.oo
        return sympy.Float(e)
    elif isinstance(e, sympy.Expr):
        if not getattr(e, "is_number", False):
            raise AssertionError(e)
        # NaNs can occur when doing things like 0 * sympy.oo, but it is better
        # if the operator notices this and takes care of it, because sometimes
        # the NaN is inappropriate (for example, for ints, the [-oo, oo] range
        # should go to zero when multiplied with [0, 0])
        if e == sympy.nan:
            raise AssertionError("sympy expression is NaN")
        return e
    elif isinstance(e, BooleanAtom):
        return e
    else:
        raise AssertionError(f"not simple sympy type {type(e)}: {e}")