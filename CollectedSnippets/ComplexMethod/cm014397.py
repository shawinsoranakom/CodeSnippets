def bound_sympy(
    expr: sympy.Expr, ranges: dict[sympy.Symbol, ValueRanges] | None = None
) -> ValueRanges:
    log.debug(
        "bound_sympy(%s)%s",
        expr,
        LazyString(
            lambda: (
                "\n"
                + "\n".join(
                    f"  {k}: {r}" for k, r in ranges.items() if k in expr.free_symbols
                )
                if ranges
                else ""
            )
        ),
    )
    if isinstance(expr, sympy.Number):
        return ValueRanges.wrap(expr)

    ranges = ranges or {}

    # If there's a tracing context, augment available constrained ranges.
    context = torch._guards.TracingContext.try_get()
    if context and context.fake_mode and context.fake_mode.shape_env:
        if ranges:
            ranges = {**context.fake_mode.shape_env.var_to_range, **ranges}
        else:
            ranges = context.fake_mode.shape_env.var_to_range

    def missing_handler(s):
        if s.is_integer:  # type: ignore[attr-defined]
            if s.is_positive:  # type: ignore[attr-defined]
                vr = ValueRanges(1, int_oo)
            elif s.is_nonnegative:  # type: ignore[attr-defined]
                vr = ValueRanges(0, int_oo)
            else:
                vr = ValueRanges.unknown_int()
        else:
            # Don't bother trying very hard here
            vr = ValueRanges.unknown()
        return vr

    return sympy_interp(
        SymPyValueRangeAnalysis, ranges, expr, missing_handler=missing_handler
    )