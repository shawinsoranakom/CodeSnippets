def _get_updated_range_constraints(
    gm: torch.fx.GraphModule,
    old_range_constraints: "dict[sympy.Symbol, Any] | None" = None,
) -> "dict[sympy.Symbol, Any]":
    if old_range_constraints is None:
        raise AssertionError("old_range_constraints must not be None")

    shape_env = _get_shape_env(gm)
    if shape_env is None:
        return {}

    range_constraints = copy.copy(old_range_constraints)
    range_constraints = {
        k: v for k, v in range_constraints.items() if k not in shape_env.replacements
    }
    # Only when we have an unbacked symint, and it's used as constructor inputs,
    # runtime_var_to_range will make a difference compated to var_to_range.
    # e.g. [2, oo) -> [0, oo)
    for k, v in shape_env.var_to_range.items():
        if k not in shape_env.replacements and k not in range_constraints:
            range_constraints[k] = v
    return range_constraints