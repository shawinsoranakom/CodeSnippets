def get_pw_red_splits(
    n: "SchedulerNode",
    pointwise_numel: sympy.Expr,
    red_numel: sympy.Expr,
    none_if_not_divisible: bool = False,
) -> tuple[VarsAndRanges, VarsAndRanges] | None:
    if n.is_reduction() or sympy_product(n._body.sizes[0]) == pointwise_numel:
        # pyrefly: ignore [bad-return]
        return (
            (n._body.iter_vars, n._body.sizes[0]),
            (n._body.reduce_vars, n._body.sizes[1]),
        )  # type: ignore[return-value]

    assert get_hint(sympy_product(n._body.sizes[0])) == get_hint(
        pointwise_numel * red_numel
    )  # type: ignore[operator]
    i = len(n._body.sizes[0]) - 1
    prod = 1
    while i >= 0:
        prod *= n._body.sizes[0][i]
        if prod == red_numel:
            break
        i -= 1

    if i >= 0:
        pw_splits = n._body.sizes[0][0:i]
        iter_vars = n._body.iter_vars[0:i]

        red_splits = n._body.sizes[0][i:]
        red_vars = n._body.iter_vars[i:]
        return (iter_vars, pw_splits), (red_vars, red_splits)  # type: ignore[return-value]

    if none_if_not_divisible:
        return None
    else:
        # pyrefly: ignore [bad-return]
        return (
            (n._body.iter_vars, n._body.sizes[0]),
            (n._body.reduce_vars, n._body.sizes[1]),
        )