def _canonicalize_bool_expr_impl(expr: SympyBoolean) -> SympyBoolean:
    """
    After canonicalization, we are guaranteed to have eliminated Ge/Gt relations
    (rewriting them to Le/Lt, respectively).
    """
    if isinstance(expr, (sympy.And, sympy.Or)):
        return type(expr)(*map(canonicalize_bool_expr, expr.args))

    opposite = {sympy.Gt: sympy.Lt, sympy.Ge: sympy.Le}
    t: type[Any]
    if isinstance(expr, tuple(opposite.keys())):
        rhs = expr.lhs - expr.rhs  # type: ignore[attr-defined]
        t = opposite[type(expr)]  # type: ignore[index]
    else:
        if not isinstance(expr, (sympy.Lt, sympy.Le, sympy.Eq, sympy.Ne)):
            raise AssertionError(f"Expected Lt/Le/Eq/Ne, got {type(expr)}")
        rhs = expr.rhs - expr.lhs
        t = type(expr)

    def is_neg(t: sympy.Expr) -> bool:
        return (t.is_Number and t.is_negative) or (
            isinstance(t, sympy.Mul) and t.args[0].is_Number and t.args[0].is_negative
        )

    lhs = S.Zero
    rhs = _reduce_to_lowest_terms(rhs)
    if isinstance(rhs, sympy.Add):
        pos = []
        neg = []
        for term in rhs.args:
            if is_neg(term):
                neg.append(-term)
            else:
                pos.append(term)
        # these are already sorted
        rhs = _sympy_from_args(sympy.Add, pos, sort=False, is_commutative=True)
        # the terms were changed, so needs a sorting
        lhs = _sympy_from_args(sympy.Add, neg, sort=True, is_commutative=True)
    elif is_neg(rhs):
        # lhs == 0
        lhs, rhs = -rhs, S.Zero
    # We don't have to evaluate here because lhs, rhs came from a Boolean
    # and it was already simplified
    return t(lhs, rhs, evaluate=False)