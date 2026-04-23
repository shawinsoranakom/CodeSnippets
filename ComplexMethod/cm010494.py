def _compute_stride(
    old_shape: Sequence[IntLikeType],
    old_stride: Sequence[IntLikeType],
    new_shape: Sequence[IntLikeType],
    size_oblivious: bool = False,
) -> list[IntLikeType] | None:
    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        guard_or_true,
        sym_eq,
    )

    def maybe_guard_or_false(x: Any) -> Any:
        if size_oblivious:
            return guard_or_false(x)

        return x

    def maybe_guard_or_true(x: Any) -> Any:
        if size_oblivious:
            return guard_or_true(x)

        return x

    if len(old_shape) == 0:
        return [1] * len(new_shape)

    numel = reduce(operator.mul, old_shape, 1)
    zero_numel = maybe_guard_or_false(numel == 0)
    if zero_numel and maybe_guard_or_false(sym_eq(old_shape, new_shape)):
        return list(old_stride)

    new_stride: list[IntLikeType] = [0] * len(new_shape)

    if zero_numel:
        for view_d in range(len(new_shape) - 1, -1, -1):
            if view_d == len(new_shape) - 1:
                new_stride[view_d] = 1
            else:
                new_stride[view_d] = (
                    max(new_shape[view_d + 1], 1) * new_stride[view_d + 1]
                )
        return new_stride

    view_d = len(new_shape) - 1
    # Annotate type here to support type checking
    chunk_base_stride: IntLikeType = old_stride[-1]
    tensor_numel: IntLikeType = 1
    view_numel: IntLikeType = 1

    for tensor_d in range(len(old_shape) - 1, -1, -1):
        tensor_numel *= old_shape[tensor_d]

        if tensor_d == 0 or (
            maybe_guard_or_true(old_shape[tensor_d - 1] != 1)
            and maybe_guard_or_true(
                old_stride[tensor_d - 1] != tensor_numel * chunk_base_stride
            )
        ):
            while view_d >= 0 and (
                maybe_guard_or_true(view_numel < tensor_numel)
                or maybe_guard_or_false(new_shape[view_d] == 1)
            ):
                new_stride[view_d] = view_numel * chunk_base_stride
                view_numel *= new_shape[view_d]
                view_d -= 1

            if maybe_guard_or_true(view_numel != tensor_numel):
                return None

            if tensor_d > 0:
                chunk_base_stride = old_stride[tensor_d - 1]
                tensor_numel = 1
                view_numel = 1
    if view_d != -1:
        return None
    return new_stride