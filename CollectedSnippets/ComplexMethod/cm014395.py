def sympy_interp(
    analysis,
    env: dict[sympy.Symbol, Any],
    expr: sympy.Expr | SympyBoolean,
    *,
    index_dtype=torch.int64,
    missing_handler=None,
):
    # Handle base cases
    dtype = None
    if isinstance(expr, BooleanAtom):
        dtype = torch.bool
    elif isinstance(expr, sympy.Integer):
        dtype = torch.int64
    elif isinstance(expr, sympy.Number):
        dtype = torch.double

    if dtype is not None:
        return analysis.constant(expr, dtype)
    elif isinstance(expr, sympy.Symbol):
        if (r := env.get(expr, _nil)) is not _nil:
            return r
        elif missing_handler:
            return missing_handler(expr)
        else:
            raise KeyError(expr)

    # Recursive case
    return _run_sympy_handler(
        analysis,
        [
            sympy_interp(
                analysis,
                env,
                arg,
                index_dtype=index_dtype,
                missing_handler=missing_handler,
            )
            for arg in expr.args
        ],
        expr,
        index_dtype=index_dtype,
    )