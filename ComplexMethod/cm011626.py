def check_contiguous_sizes_strides(sizes, strides, false_if_dde=False):
    """
    Performs an equality check between actual stride & expected stride (based on composed sizes),
    handling contiguous stride representations:
    e.g. torch.empty(u0, u1, u2).contiguous().stride() -> (Max(1, u1) * Max(1, u2), Max(1, u2), 1)
    and we'd like to treat this equal to (u1 * u2, u2, 1) for comparison purposes.
    """

    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        guard_or_true,
        is_nested_int,
    )

    def eval_eager(x):
        return bool(x)

    maybe_guard_or_false = guard_or_false if false_if_dde else eval_eager
    maybe_guard_or_true = guard_or_true if false_if_dde else eval_eager

    expected_stride = 1
    expected_stride_max = 1

    # pyrefly: ignore [bad-assignment]
    for x, y in reversed(tuple(zip(sizes, strides))):
        # Skips checking strides when a dimension has length 1.
        if maybe_guard_or_false(x == 1):
            continue

        if maybe_guard_or_true(y != expected_stride) and maybe_guard_or_true(
            y != expected_stride_max
        ):
            return False

        #  We symbolically check both paths to maximize the cases where this function
        #  returns true. This is because make_contiguous_strides_for adds the max
        #  symbolically, and in some other situations the max might not be there.
        #  And we want to ensure we return true in both cases.
        expected_stride_max *= x if is_nested_int(x) else sym_max(x, 1)  # type:ignore[assignment]

        expected_stride *= x

    return True