def get_max_alignment(inductor_layout: Layout) -> int:
    """
    Returns the max alignment (in terms of number of elements) for a given Inductor Layout.
    """

    dtype = inductor_layout.dtype
    size = inductor_layout.size
    offset = inductor_layout.offset

    def is_static_int(number: object) -> TypeIs[int | sympy.Integer]:
        return isinstance(number, (int | sympy.Integer))

    def a_factor_of(x, alignment):
        if is_static_int(x) and is_static_int(alignment):
            return x % alignment == 0
        rem = sympy.Mod(x, alignment)
        return V.graph.sizevars.evaluate_expr(sympy.Eq(rem, 0))

    try:
        contiguous_dim = inductor_layout.stride.index(1)
    except ValueError:
        # No dim with stride 1 found, return 1
        return 1
    alignments = get_alignments(dtype)
    for alignment in alignments:
        if not a_factor_of(size[contiguous_dim], alignment) or not a_factor_of(
            offset, alignment
        ):
            continue
        if all(
            (dim == contiguous_dim)
            or a_factor_of(inductor_layout.stride[dim], alignment)
            for dim in range(len(size))
        ):
            return alignment
    return 1