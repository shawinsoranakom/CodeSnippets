def _select_min_redistribute_cost(
    costs: list[torch.types.FloatLikeType],
    strategies: list[OpSpec],
    op_schema: OpSchema | None = None,
) -> int:
    """
    Given a list of costs and corresponding op strategies, selects the minimum cost strategy, returning the index.
    If unbacked symbols are involved, replaces them with known upper-bound values, falling back to hardcoded values.
    """
    from torch.fx.experimental.symbolic_shapes import (
        free_unbacked_symbols,
        is_concrete_float,
    )
    from torch.utils._sympy.interp import sympy_interp
    from torch.utils._sympy.numbers import int_oo
    from torch.utils._sympy.reference import PythonReferenceAnalysis

    int_fallback = 8192
    free_unbacked = list(set(chain(*[free_unbacked_symbols(cost) for cost in costs])))

    # Easy path: no unbacked shapes involved, choose min cost strategy.
    # Doing the hard path for backed could also make sense?
    if all(is_concrete_float(c) for c in costs) or not free_unbacked:
        return costs.index(min(costs))

    # Figure out heuristic hints for unbacked shapes.
    # If available, use shape upper bound. If not, fallback to some integer (inductor size-hinting style).
    shape_env = next(iter(x for x in costs if not is_concrete_float(x))).node.shape_env  # type: ignore[arg-type]
    replacements = {}
    for sym in free_unbacked:
        # TODO(laithsakka): unify with optimization_hint API
        if (hint := shape_env.var_to_hint_override.get(sym)) is not None:
            replacements[sym] = hint
        elif (upper := shape_env.bound_sympy(sym).upper) is not int_oo:
            replacements[sym] = upper
        else:
            replacements[sym] = int_fallback

    # Use replacements for redistribute cost hints
    proxy_costs = [
        float(cost)
        if is_concrete_float(cost)
        else sympy_interp(
            PythonReferenceAnalysis,
            replacements,
            cost.node.expr.xreplace(replacements),  # type: ignore[arg-type]
        )
        for cost in costs
    ]
    min_cost = min(proxy_costs)
    strategy_index = proxy_costs.index(min_cost)

    if op_schema:
        log.debug(
            "%s",
            LazyString(
                _format_unbacked_hinting_log,
                op_schema,
                strategies,
                strategy_index,
                replacements,
            ),
        )
    return strategy_index