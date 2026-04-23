def apply_var_mapping(
    iter_vars: list[sympy.Symbol],
    red_vars: list[sympy.Symbol],
    norm_pw_vars: list[sympy.Symbol],
    norm_red_vars: list[sympy.Symbol],
    new_ranges: list[list[sympy.Expr]],
    return_getters_groups: list[list[Callable[[list[sympy.Expr]], sympy.Expr]]],
) -> dict[sympy.Symbol, sympy.Expr]:
    """Maps original variables to expressions using normalized variables."""

    # the output of split_iteration_range is a new_ranges, return_getters_groups
    # new_ranges is a flattened list of ranges corresponding to the new pw and red vars
    # for example, taking in pw vars of range (6, 6) to normalized range [36],
    # new_ranges would be [[6, 6]]
    # There is a return_getter callable for each input iter_var and red_vars.
    # if you flatten out all of the ranges, and create a variable for each index,
    # then applying the flattening vars to the callables in return_getters_groups
    # gives you the mapping from input vars -> flattened vars.
    # From there, we can compute the output, normalized variables.
    # For instance [6, 6] corresponding to flat vars v0, v1 will be
    # v0 + 6 * v1

    # Create flattened iteration variables
    num_vars = sum(len(s) for s in new_ranges)
    flat_vars = sympy.symbols(f"v_0:{num_vars}")
    count = 0

    if len(iter_vars) == 0 and len(red_vars) == 0:
        return {}

    assert len(new_ranges) == len(norm_pw_vars + norm_red_vars)
    apply_groups = []
    for group in return_getters_groups:
        apply_groups.append([g(flat_vars) for g in group])

    iter_vars_to_flat_vars = {}
    for i, (group, var_group) in enumerate(
        zip(apply_groups, (iter_vars, red_vars), strict=True)
    ):
        # if the node has sizes (p0, 1) and the fused node is (p0, r0)
        # the reduction var gets filled in for split_iteration_range
        if len(group) != len(var_group):
            assert i == 1
            assert len(var_group) == 0
            continue

        iter_vars_to_flat_vars.update({v: g for g, v in zip(group, var_group)})

    count = 0
    flat_vars_to_new_vars = {}
    for new_range, new_var in zip(
        new_ranges, norm_pw_vars + norm_red_vars, strict=True
    ):
        range_vars = []
        for _ in range(len(new_range)):
            range_vars.append(flat_vars[count])
            count += 1

        prod = 1
        for i in range(len(new_range) - 1, -1, -1):
            flat_vars_to_new_vars[range_vars[i]] = new_var * prod
            prod = new_range[i] * prod

    return {
        k: sympy_subs(v, flat_vars_to_new_vars)
        for k, v in iter_vars_to_flat_vars.items()
    }