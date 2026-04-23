def analyze_expression_properties(
    expr: sympy.Expr, var: sympy.Symbol
) -> tuple[_IntLike | None, _IntLike | None]:
    """Analyze an expression to determine its range and reconstruction multiplier."""
    # ModularIndexing(var, divisor, modulo) = (var // divisor) % modulo
    if isinstance(expr, ModularIndexing):
        x, div, mod = expr.args
        if static_eq(x, var):
            return mod, div  # Range is mod, multiplier is div

    # FloorDiv cases
    if isinstance(expr, FloorDiv):
        base, divisor = expr.args

        # FloorDiv(ModularIndexing(var, 1, mod), div) = (var % mod) // div
        if isinstance(base, ModularIndexing):
            x, inner_div, mod = base.args
            if static_eq(x, var) and static_eq(inner_div, 1):
                range_val = FloorDiv(mod, divisor)
                return range_val, divisor  # Range is mod//div, multiplier is div

        # FloorDiv(var, divisor) = var // divisor (unbounded)
        elif static_eq(base, var):
            return None, divisor  # Unbounded range, multiplier is div

    return None, None