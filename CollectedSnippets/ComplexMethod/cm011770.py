def solve_for_tiling(expr: sympy.Expr) -> sympy.Expr | None:
    """
    Giving an expr with a single free symbol, try to find a tiling that would
    make the expression coalesced with respect to that symbol.

    Tiling an expression `x` by `y` means that the expression will now be indexed
    by both the original (x) and by (x * y). So we are looking for a
    multiplicative factor that will make ((x + 1) * y) - (x * y) == 1.

    To simplify things for sympy, we'll try just x * y == 1, check x(1) and x(0).
    """

    if len(expr.free_symbols) != 1:
        return None

    free_symbol = next(iter(expr.free_symbols))

    def _solve_simple_expr(expr: sympy.Expr) -> sympy.Expr | None:
        assert not expr.has(ModularIndexing) and not expr.has(FloorDiv)
        if len(expr.free_symbols) != 1:
            return None

        out = try_solve(sympy.Eq(expr, 1), free_symbol)
        if not out or not out[1].is_constant():
            return None
        return out[1]

    # Sympy solving is very limited with ModularIndexing and FloorDiv,
    # but good otherwise.
    if not expr.has(ModularIndexing) and not expr.has(FloorDiv):
        return _solve_simple_expr(expr)

    required_values = []
    eq_1_expressions = []

    # very piecemeal solution if ModularIndexing or FloorDiv involved.
    # Look for terms we'll try to make 0, and then other terms we'll try to make 1.
    # Expand as needed.
    for arg in sympy.Add.make_args(expr):
        # Try to make mul terms 0
        if isinstance(arg, sympy.Mul):
            seen = False
            # TODO - only need one of these to be solvable to zero
            for mul_arg in arg.args:
                out = solve_for_zero(mul_arg)
                if out is None:
                    continue

                assert out.is_constant()
                seen = True
                required_values.append(out)

            if not seen:
                return None
        else:
            eq_1_expressions.append(arg)

    if not eq_1_expressions:
        return None

    eq_1_expr = sum(eq_1_expressions)

    def indexing_div_rep(
        x: sympy.Expr,
        y: sympy.Expr,
        z: sympy.Expr | None = None,
    ) -> sympy.Expr:
        return x / y

    # For the purposes of tiling/coalesced access, approximate ModularIndexing and FloorDiv
    # then check later
    # pyrefly: ignore [missing-attribute]
    eq_1_expr_simplified = eq_1_expr.replace(ModularIndexing, indexing_div_rep).replace(
        FloorDiv, indexing_div_rep
    )

    out = _solve_simple_expr(eq_1_expr_simplified)

    # since we approximated FloorDiv/ModularIndexing, double check here
    if not out or sympy_subs(eq_1_expr, {free_symbol: out}) != 1:
        return None

    required_values.append(out)

    if len(OrderedSet(required_values)) == 1:
        return required_values[0]

    return None