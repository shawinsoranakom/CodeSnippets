def are_strides_like_channels_last_or_false(
    shape: Sequence[int], strides: Sequence[int]
) -> bool:
    from torch.fx.experimental.symbolic_shapes import (
        guard_or_true,
        statically_known_true,
    )

    ndim = len(shape)

    if ndim == 4:
        # Check for channels_last_2d
        dim_order = [1, 3, 2, 0]
    elif ndim == 5:
        # Check for channels_last_3d
        dim_order = [1, 4, 3, 2, 0]
    else:
        return False

    if guard_or_true(strides[1] == 0):
        return False

    min = 0
    for d in dim_order:
        if guard_or_true(shape[d] == 0):
            return False
        if guard_or_true(strides[d] < min):
            return False
        if d == 0 and min == strides[1]:
            return False
        min = strides[d]
        # Only multiply by shape[d] when size >= 1, matching C++ logic
        # shape[d]!=0 hence we know its >=1 here
        min *= shape[d]
    return True