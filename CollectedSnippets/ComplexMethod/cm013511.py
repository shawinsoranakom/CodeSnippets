def _fast_expand(expr: _SympyT) -> _SympyT:
    """
    A faster implementation of sympy's expand function for common cases.

    This function expands expressions like (a+b)^n or (a+b)*(c+d) into sums of products,
    but avoids the expensive checks and features of sympy's full expand implementation.
    It only recreates objects when necessary to avoid expensive operations.

    Args:
        expr: A sympy expression to expand

    Returns:
        The expanded expression
    """

    # The expand algorithm in sympy is slow due to all the features is supports
    # For eg: e^(-x)*(x-1)/(x+1) is expanded to (x-1)/(e^x + e^x*x) if x is
    # positive and (e^(-x)*x-e^(-x))/(x+1) if x is negative. We do not implement
    # such features here to avoid expensive checks. We also make sure that we
    # only re-create the objects if any of the args changed to avoid expensive
    # checks when re-creating objects.
    new_args = [_fast_expand(arg) for arg in expr.args]  # type: ignore[arg-type]
    # pyrefly: ignore [missing-attribute]
    if any(arg is not new_arg for arg, new_arg in zip(expr.args, new_args)):
        # pyrefly: ignore [missing-attribute]
        return _fast_expand(expr.func(*new_args))

    # pyrefly: ignore [missing-attribute]
    if expr.is_Pow:
        base: sympy.Expr
        exp: sympy.Expr
        base, exp = expr.args  # type: ignore[assignment]
        if exp.is_Integer and base.is_Add:
            if exp > 1:
                return sympy.expand_multinomial(expr, deep=False)
            elif exp < 0:
                return S.One / sympy.expand_multinomial(S.One / expr, deep=False)
    # pyrefly: ignore [missing-attribute]
    elif expr.is_Mul:
        num: list[sympy.Expr] = []
        den: list[sympy.Expr] = []
        # pyrefly: ignore [missing-attribute]
        for arg in expr.args:
            if arg.is_Pow and arg.args[1] == -1:
                den.append(S.One / arg)  # type: ignore[operator, arg-type]
            else:
                num.append(arg)  # type: ignore[arg-type]

        num, num_changed = _expandsums(num)
        den, den_changed = _expandsums(den)
        if num_changed or den_changed:
            return num / den

    return expr