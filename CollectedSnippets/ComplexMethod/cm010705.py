def _reflection_pad_backward(grad_output, x, padding):
    dim = len(padding) // 2

    dhw = [h - 1 for h in x.shape[-dim:]]

    padding_left = [padding[2 * (dim - 1 - i)] for i in range(dim)]
    padding_right = [padding[2 * (dim - 1 - i) + 1] for i in range(dim)]

    indices = []
    for i in range(x.ndim):
        view_shape = [1] * x.ndim
        view_shape[i] = -1
        indices.append(torch.arange(x.shape[i], device=x.device).view(view_shape))

    b = indices[:-dim]
    xyz = indices[-dim:]

    def index_range_condition(index_range):
        i, lb, ub = index_range
        return torch.logical_and(i >= lb, i <= ub)

    # Areas after reflection:
    #
    #   top-left    |   top     |   top-right
    # -----------------------------------------
    #   left        |   center  |   right
    # -----------------------------------------
    #   bottom-left |   bottom  |   bottom-right
    #
    # The center area is the original matrix. Other areas are reflections.

    center = [xyz[i] + padding_left[i] for i in range(dim)]
    left_reflect = [padding_left[i] - xyz[i] for i in range(dim)]
    right_reflect = [2 * dhw[i] + padding_left[i] - xyz[i] for i in range(dim)]

    # Accumulate gradients from different areas
    # If some of the padding is negative, center load is not always valid
    range_c = [
        (center[i], 0, dhw[i] + padding_left[i] + padding_right[i]) for i in range(dim)
    ]
    cond = functools.reduce(
        aten.logical_and, [index_range_condition(range_c[i]) for i in range(dim)]
    )
    grad = aten._unsafe_masked_index(grad_output, cond, b + center, 0.0)

    def accumulate(grad, out, index_ranges):
        # If the upper bound is less than the lower bound, we can get rid of one accumulation.
        # This happens when the padding size is zero.
        for i in range(dim):
            upper_less_than_lower = index_ranges[i][2] < index_ranges[i][1]
            if isinstance(upper_less_than_lower, bool) and upper_less_than_lower:
                return grad

        cond = functools.reduce(
            aten.logical_and,
            [index_range_condition(index_range) for index_range in index_ranges],
        )
        g = aten._unsafe_masked_index(grad_output, cond, b + out, 0.0)
        return grad + g

    for area in itertools.product(*[[-1, 0, 1] for _ in range(dim)]):
        if area == tuple([0] * dim):
            # center, this is already done.
            continue

        outs = []
        index_ranges = []

        for i in range(dim):
            if area[i] == 0:
                out = center[i]
                index_range = range_c[i]
            elif area[i] == -1:
                out = left_reflect[i]
                index_range = (xyz[i], 1, padding_left[i])
            elif area[i] == 1:
                out = right_reflect[i]
                index_range = (xyz[i], dhw[i] - padding_right[i], dhw[i] - 1)

            outs.append(out)  # type: ignore[possibly-undefined]
            index_ranges.append(index_range)  # type: ignore[possibly-undefined]

        grad = accumulate(grad, outs, index_ranges)

    return grad