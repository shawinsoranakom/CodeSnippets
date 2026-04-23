def triton_reshape(
    value: str, old_shape: Sequence[sympy.Expr], new_shape: Sequence[sympy.Expr]
) -> str:
    """Workaround https://github.com/triton-lang/triton/issues/2836"""
    assert isinstance(old_shape, list) and isinstance(new_shape, list)

    old_shape_str = [V.kernel.index_to_str(shape) for shape in old_shape]
    new_shape_str = [V.kernel.index_to_str(shape) for shape in new_shape]

    if old_shape_str == new_shape_str:
        return value
    if [s for s in new_shape_str if s != "1"] != old_shape_str:
        return f"tl.reshape({value}, [{', '.join(new_shape_str)}])"
    # rewrite to [:, None] syntax, which is less buggy
    idx = 0
    expand = []
    for size in new_shape_str:
        if idx < len(old_shape_str) and size == old_shape_str[idx]:
            expand.append(":")
            idx += 1
        else:
            assert size == "1"
            expand.append("None")
    assert idx == len(old_shape_str)
    return f"{value}[{', '.join(expand)}]"