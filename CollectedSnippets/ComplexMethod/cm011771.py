def find_coalesced_var(
    index: sympy.Expr, var_ranges: dict[sympy.Expr, int]
) -> sympy.Expr | None:
    """
    Try to find the symbol which coalesces this index
    """
    top_level_terms = sympy.Add.make_args(index)
    for v in var_ranges:
        if v in top_level_terms:
            return v

    # Approximate analysis by evaluating at 1 and 0
    variables: dict[sympy.Symbol, int] = {}
    for v in index.free_symbols:
        if v in var_ranges:
            variables[v] = 0
        else:
            variables[v] = get_hint(v)

    zero_index = sympy_subs(index, variables)
    for v in var_ranges:
        variables[v] = 1
        try:
            new_val = sympy_subs(index, variables)
        except ZeroDivisionError:
            loop_tiling_log.info("zero division error %s %s", index, variables)
            continue
        if new_val - zero_index == 1:
            variables[v] = 2
            # in some more complex expressions, 0->1 will be coalesced,
            # but not 1->2
            if (sympy_subs(index, variables) - new_val) == 1:
                return v
        variables[v] = 0

    return None