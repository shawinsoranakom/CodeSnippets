def _collapse_view_helper(
    a: TensorLikeType, start: int, end: int, must_be_valid: str | None
) -> tuple[ShapeType | None, StrideType | None]:
    if not isinstance(a, TensorLike):
        raise AssertionError(f"a must be TensorLike, got {type(a)}")  # mypy

    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        guard_or_true,
        sym_and,
        sym_or,
    )

    _validate_collapse_args(a, start, end)

    # Special-case for zero dimensional tensors
    if a.ndim == 0:
        shape = (1,)
        strides = (1,)
    else:
        shape = a.shape  # type: ignore[assignment]
        strides = a.stride()  # type: ignore[assignment]

    if a.ndim == 0 or (end == start):
        return shape, strides

    valid_op = True
    if guard_or_false(a.numel() != 0):
        for idx in range(end - 1, start - 1, -1):
            valid_op = sym_and(
                valid_op,
                sym_or(
                    shape[idx] == 1,
                    shape[idx + 1] == 1,
                    strides[idx] == strides[idx + 1] * shape[idx + 1],
                ),
            )  # type: ignore[assignment]

            # early exit if we already know its invalid.
            if guard_or_false(valid_op is False):
                break

    # for unbacked this become a runtime assertion.
    valid_op = sym_or(valid_op, a.numel() == 0)

    if must_be_valid:
        torch._check(valid_op, lambda: must_be_valid)
    else:
        if not guard_or_false(valid_op):
            return None, None

    # compute stride
    stride = strides[end]
    for idx in range(end - 1, start - 1, -1):
        if shape[idx] != 1:
            # TODO with unbacked we should really exclude when shape[idx] == 1
            # something like
            # min(stride[end], torch.ite(shape[x]!=1,stride[idx], inf), ...)
            stride = min(stride, strides[idx])

    # compute length
    length = shape[end]
    if guard_or_true(length != 0):
        for idx in range(end - 1, start - 1, -1):
            if guard_or_false(shape[idx] == 0):
                length = 0
                stride = 0
                break
            length = length * shape[idx]
    else:
        stride = 0

    new_shape = shape[:start] + (length,) + shape[end + 1 :]
    new_strides = strides[:start] + (stride,) + strides[end + 1 :]

    # NOTE: when the input has no elements it's restrided as if it were contiguous
    # except for unbacked.
    if guard_or_false(a.numel() == 0):
        new_strides = utils.make_contiguous_strides_for(new_shape)

    return new_shape, new_strides