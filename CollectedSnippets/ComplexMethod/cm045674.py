def types_lca(
    left: DType, right: DType, *, raising: bool, int_float_compatible: bool = True
) -> DType:
    """LCA of two types."""
    if isinstance(left, Optional) or isinstance(right, Optional):
        return Optional(
            types_lca(
                unoptionalize(left),
                unoptionalize(right),
                raising=raising,
                int_float_compatible=int_float_compatible,
            )
        )
    elif isinstance(left, (Tuple, List)) and isinstance(right, (Tuple, List)):
        if left == ANY_TUPLE or right == ANY_TUPLE:
            return ANY_TUPLE
        if isinstance(left, List) and isinstance(right, List):
            return List(
                types_lca(
                    left.wrapped,
                    right.wrapped,
                    raising=raising,
                    int_float_compatible=int_float_compatible,
                )
            )
        largs, rargs = broadcast_tuples(left, right)
        if len(largs) != len(rargs):
            if raising:
                raise TypeError
            else:
                return ANY_TUPLE
        return Tuple(
            *[
                types_lca(
                    l_arg,
                    r_arg,
                    raising=raising,
                    int_float_compatible=int_float_compatible,
                )
                for l_arg, r_arg in zip(largs, rargs)
            ]
        )
    elif isinstance(left, Array) and isinstance(right, Array):
        if left.n_dim is None or right.n_dim is None:
            n_dim = None
        elif left.n_dim == right.n_dim:
            n_dim = left.n_dim
        else:
            n_dim = None
        if left.wrapped == ANY or right.wrapped == ANY:
            wrapped = ANY
        elif left.wrapped == right.wrapped:
            wrapped = left.wrapped
        else:
            if raising:
                raise TypeError
            else:
                wrapped = ANY
        return Array(n_dim=n_dim, wrapped=wrapped)
    elif isinstance(left, Pointer) and isinstance(right, Pointer):
        if left.args is None or right.args is None:
            return ANY_POINTER
        if len(left.args) != len(right.args):
            if raising:
                raise TypeError
            else:
                return ANY_POINTER
        return Pointer(
            *[
                types_lca(left, right, raising=raising, int_float_compatible=False)
                for left, right in zip(left.args, right.args)
            ]
        )
    if dtype_issubclass(left, right, int_float_compatible=int_float_compatible):
        return right
    elif dtype_issubclass(right, left, int_float_compatible=int_float_compatible):
        return left

    if left == NONE:
        return Optional(right)
    elif right == NONE:
        return Optional(left)
    elif left == ANY or right == ANY:
        return ANY
    else:
        if raising:
            raise TypeError
        else:
            return ANY