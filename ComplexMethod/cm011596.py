def _reshape_view_helper_core_alg(
    a: TensorLikeType, shape, allow_copy: bool
) -> TensorLikeType:
    # NOTE [Reshape Algorithm]
    # This algorithm works by attempting to greedily construct the desired dimensions in
    # the output shape, left to right. It does this by, conceptually, accumulating
    # dimensions of the original tensor, also left to right, until the dimension
    # can be constructed using prims.split_dim.
    # The algorithm also has special handling for tail squeezes/unsqueezes, like
    # if a reshape from (5, 5) to (5, 5, 1) or vice versa.
    #
    # This algorithm does not flatten the original tensor and then split dims as appropriate
    # because that would create copies more often than this algorithm. flatten is the only
    # operation below which can create a view or a copy, and while it prefers creating
    # views it may sometimes create a copy if the tensor's strides do not permit a view.
    # As a result, this algorithm tries to minimize flattening.
    #
    # Note that a better version of this algorithm may exist. Regions which could be
    # flattened without creating a copy can be identified in advance, and that might
    # allow fewer flatten calls or faster short-circuiting to make a copy.
    idx = 0
    a_ = a
    for length in shape:
        # Handles tail unsqueezes
        if idx >= a_.ndim:
            if length != 1:
                raise AssertionError(
                    f"Cannot unsqueeze dimension with length {length}, expected 1"
                )
            last_dim = a_.ndim - 1
            # NOTE: using split_dim instead of unsqueeze may seem silly here,
            # but it's necessary to get the strides correct
            a_ = prims.split_dim(a_, last_dim, a_.shape[last_dim])
            idx = idx + 1
            continue

        # Skips dimensions that are already the correct length
        if length == a_.shape[idx]:
            idx = idx + 1
            continue

        accum = a_.shape[idx]
        end = idx
        while accum % length != 0:
            end += 1
            accum *= a_.shape[end]
        if end != idx:
            # NOTE: in this case multiple dimensions must be flatten to create the desired dimension
            # This flattening is why reshape sometimes creates a copy -- because flattening
            # may return a view of a copy

            # Checks if collapse can be a view and short-circuits to copying reshape if it can't
            new_shape, _new_strides = prims._collapse_view_helper(
                a_, idx, end, must_be_valid=None
            )
            if new_shape is None:
                if allow_copy:
                    return prims.reshape(a, shape)

                msg = f"Cannot view a tensor with shape {a.shape} and strides {a.stride()} as a tensor with shape {shape}!"
                raise ValueError(msg)

            a_ = flatten(a_, idx, end)

        # Splits the (possibly flattened) dimension to create the desired dim length.
        # guard_or_true is safe due to the tail unsqueeze routine.
        if accum != length:
            a_ = prims.split_dim(a_, idx, length)

        idx = idx + 1

    # Squeezes tail
    while idx < a_.ndim:
        torch._check(
            a_.shape[idx] == 1,
            lambda: f"a.size({idx}) expected to be 1 but got {a_.shape[idx]}",
        )
        a_ = squeeze(a_, idx)

    if a_ is a:
        return prims.view_of(a)
    else:
        return a_