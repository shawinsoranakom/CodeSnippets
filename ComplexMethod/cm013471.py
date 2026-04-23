def _guarding_hint_or_throw_base(
    shape_env: ShapeEnv,
    expr: sympy.Expr | sympy.Basic | int | bool,
    precomputed_replacements: dict[sympy.Expr, sympy.Symbol],
) -> int | bool:
    """
    Return a concrete integer hint for an expression that is safe to use for guarding.

    This function evaluates the expression using only backed-symbols hints. Unlike
    _optimization_hint_base(), this function does NOT use heuristics or fallback values
    for unbacked symbols.

    Use this when you need a hint value that will be used for a guarding decision.

    Args:
        shape_env: The ShapeEnv instance.
        expr: A sympy expression or integer to evaluate.
        precomputed_replacements: Precomputed replacements for PRECOMPUTED_SIZE symbols.

    Returns:
        The concrete integer value of the expression based on backed symbol hints.

    Raises:
        GuardOnDataDependentSymNode: If the expression contains unbacked symbols
        (data-dependent values) that cannot be resolved to concrete values.

    See Also:
        _optimization_hint_base: For cases where fallback/heuristic values are acceptable
            for unbacked symbols.
    """
    from torch.fx.experimental.symbolic_shapes import (
        has_free_unbacked_symbols,
        symbol_is_type,
        SymT,
    )

    # sympy.expand() doesn't work with boolean expressions like Or/And
    if isinstance(expr, sympy.Expr):
        expr = sympy.expand(expr).xreplace(shape_env.replacements)
    else:
        expr = sympy.sympify(expr).xreplace(shape_env.replacements)

    if isinstance(expr, sympy.Expr):
        expr = expr.expand(identity=True)

    result = _maybe_realize_expr(expr, None)
    if result is not None:
        return result

    if not isinstance(expr, sympy.Basic):
        raise RuntimeError("isinstance(expr, sympy.Basic)", expr, type(expr))

    if any(symbol_is_type(s, SymT.PRECOMPUTED_SIZE) for s in expr.free_symbols):  # type: ignore[attr-defined]
        expr = _sympy_subs(expr, precomputed_replacements)

    # TODO do we need sympy_subs, or just xreplace
    expr = _sympy_subs(expr, shape_env.backed_var_to_val)
    if isinstance(expr, sympy.Expr):
        expr = expr.expand(identity=True)

    if has_free_unbacked_symbols(expr):
        # Note: we could do better here and call
        # _maybe_evaluate_static(orig_expr, compute_hint=True)
        # but is it worth the overhead? probably not.
        raise shape_env._make_data_dependent_error(expr, expr)

    result = _maybe_realize_expr(expr, None)
    if result is None:
        raise RuntimeError("unexpected None!", expr)
    return result