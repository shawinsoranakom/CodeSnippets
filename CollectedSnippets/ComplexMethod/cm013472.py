def _optimization_hint_base(
    shape_env: ShapeEnv,
    expr: sympy.Expr | int,
    precomputed_replacements: dict[sympy.Expr, sympy.Symbol],
    fallback: int | None = None,
) -> int:
    """
    Return a concrete integer hint for an expression using heuristics.

    This function should be used for non-guarding based optimizations.
    It will hint unbacked symbols using user provided optimization hints.
    If not provided, fallback will be used along with some heuristics
    that try to maximize consistency with the shape environment.

    Args:
        shape_env: The ShapeEnv instance.
        expr: A sympy expression or integer to evaluate.
        precomputed_replacements: Precomputed replacements for PRECOMPUTED_SIZE symbols.
        fallback: Fallback value for unbacked symbols. If None, reads from config.

    Returns:
        A concrete integer hint for the expression.
    """
    from torch.fx.experimental.symbolic_shapes import (
        has_free_unbacked_symbols,
        symbol_is_type,
        SymT,
    )

    # Read config at call time to respect runtime patches (e.g., in tests)
    if fallback is None:
        from torch._inductor.config import unbacked_symint_fallback

        fallback = unbacked_symint_fallback

    # to have expanded (Identity free) expr stored in original
    if isinstance(expr, sympy.Expr):
        expr = expr.expand(identity=True)

    original = expr
    # sympy.expand() doesn't work with boolean expressions like Or/And
    if isinstance(expr, sympy.Expr):
        expr = expr.xreplace(shape_env.replacements)
    else:
        expr = sympy.sympify(expr).xreplace(shape_env.replacements)

    result = _maybe_realize_expr(expr, fallback)
    if result is not None:
        return result

    if isinstance(expr, sympy.Expr):
        expr = expr.expand(identity=True)

    # Replace backed symbols with their hints, leaving unbacked symbols alone.
    result = _maybe_realize_expr(expr, None)
    if result is not None:
        return result

    if not isinstance(expr, sympy.Expr):
        raise RuntimeError("isinstance(expr, sympy.Expr)", expr)

    if any(symbol_is_type(s, SymT.PRECOMPUTED_SIZE) for s in expr.free_symbols):  # type: ignore[attr-defined]
        expr = _sympy_subs(expr, precomputed_replacements)

    expr = _sympy_subs(expr, shape_env.backed_var_to_val)
    if isinstance(expr, sympy.Expr):
        expr = expr.expand(identity=True)

    result = _maybe_realize_expr(expr, fallback)
    if result is not None:
        return result

    expr = _sympy_subs(expr, shape_env.var_to_hint_override)

    result = _maybe_realize_expr(expr, fallback)
    if result is not None:
        return result

    # If unbacked symbols remain, try to substitute them using heuristics
    # that maximize consistency with the shape environment.
    if has_free_unbacked_symbols(expr):
        # Make sure to substitute with the factored version
        # e.g. 10*(s0 + u0) instead of 10*s0 + 10*u0
        if (
            isinstance(original, sympy.Expr)
            and len(original.free_symbols) <= SYMPY_FACTOR_MAX_FREE_SYMBOLS
        ):
            original = sympy.factor(original)
        expr = _sub_unbacked_exprs(shape_env, original)

    # For multiple expressions that depend on an unbacked symint,
    # we want to compute them consistently for a size hint we have chosen.
    # So, recursively compute expressions via size hints of contained symbols.
    # For example: u1 * u2 - 10 ==> fallback * fallback - 10

    if not isinstance(expr, sympy.Expr):
        raise RuntimeError(f"Expected sympy Expr, got {type(expr)}: {expr}")
    free_symbols = expr.free_symbols

    # Constrain fallback per-symbol based on var_to_range bounds
    size_dict = {}
    for s in free_symbols:
        sym_fallback = fallback
        vr = shape_env.var_to_range.get(s, None)
        if vr is not None:
            if isinstance(vr.lower, (int, sympy.Integer)):
                sym_fallback = max(sym_fallback, int(vr.lower))
            if isinstance(vr.upper, (int, sympy.Integer)):
                sym_fallback = min(sym_fallback, int(vr.upper))
        size_dict[s] = sym_fallback

    try:
        final_result = expr.subs(size_dict)
    except ZeroDivisionError:
        # Expressions like ModularIndexing(x, u1, 4) crash during subs()
        # when u1 is substituted with 0, because sympy eagerly evaluates
        # (x // 0) % 4.  This can happen when an unbacked symbol with
        # var_to_range lower=0 is used as a divisor (e.g. from
        # _dynamic_reshape_indexer) and the fallback also maps to 0.
        # Return fallback in that case.
        return fallback if fallback is not None else 0

    final_result = _maybe_realize_expr(final_result, fallback)
    if final_result is None:
        raise RuntimeError(f"Failed to realize expression to int: {expr}")

    return final_result