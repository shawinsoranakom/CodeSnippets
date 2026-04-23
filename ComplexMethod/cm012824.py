def _compare_and_swap_with_index(
    x,
    idxs,
    rnumel,
    flip,
    i: tl.constexpr,
    n_dims: tl.constexpr,
    stable: tl.constexpr,
    descending: tl.constexpr,
):
    n_outer: tl.constexpr = x.numel >> n_dims
    shape: tl.constexpr = [n_outer * 2**i, 2, 2 ** (n_dims - i - 1)]

    idtype = tl.core.get_int_dtype(bitwidth=x.dtype.primitive_bitwidth, signed=True)

    y = tl.reshape(x, shape)
    iy = y.to(idtype, bitcast=True)
    # slice left/right with 'stride' 2**(n_dims - i - 1)
    right_mask = tl.arange(0, 2)[None, :, None].to(idtype)
    left_mask = (1 - right_mask).to(idtype)
    ileft = tl.broadcast_to(tl.sum(iy * left_mask, 1).to(idtype)[:, None, :], shape)
    iright = tl.broadcast_to(tl.sum(iy * right_mask, 1).to(idtype)[:, None, :], shape)
    ileft = tl.reshape(ileft, x.shape)
    iright = tl.reshape(iright, x.shape)
    left = ileft.to(x.dtype, bitcast=True)
    right = iright.to(x.dtype, bitcast=True)

    # idx
    y_idx = tl.reshape(idxs, shape)
    left_idx = tl.broadcast_to(
        tl.sum(y_idx * left_mask.to(y_idx.dtype), 1)[:, None, :], shape
    )
    right_idx = tl.broadcast_to(
        tl.sum(y_idx * right_mask.to(y_idx.dtype), 1)[:, None, :], shape
    )
    left_idx = tl.reshape(left_idx, x.shape)
    right_idx = tl.reshape(right_idx, x.shape)

    # valid
    if rnumel is None:
        left_valid_mask = tl.full(x.shape, True, tl.int1)
        right_valid_mask = tl.full(x.shape, True, tl.int1)
    else:
        left_valid_mask = left_idx < rnumel
        right_valid_mask = right_idx < rnumel

    # actual compare-and-swap
    ix = x.to(idtype, bitcast=True)

    # sort treats nan as having the higher value. comparisons with nan always return False.
    # to align with sort semantics, we need to update descending to check if right_isnan,
    # and ascending to check if left_isnan.
    left_isnan = left != left
    right_isnan = right != right

    if descending:
        cond = left < right
        if is_floating(left):
            if not stable:
                cond = cond | right_isnan
            else:
                cond = cond | (right_isnan & (~left_isnan))

    else:
        cond = left > right
        if is_floating(left):
            if not stable:
                cond = cond | left_isnan
            else:
                cond = cond | (left_isnan & (~right_isnan))

    if stable:
        # When stable sorting, tie break by index
        eq = left == right
        if is_floating(left):
            eq = eq | (left_isnan & right_isnan)
        cond = cond | (eq & (left_idx > right_idx))

    cond = (right_valid_mask > left_valid_mask) | (
        (right_valid_mask == left_valid_mask) & cond
    )
    cond = (cond ^ flip).to(tl.int1)
    ret = ix ^ tl.where(cond, ileft ^ iright, tl.zeros_like(ix))
    new_idxs = idxs ^ tl.where(cond, left_idx ^ right_idx, tl.zeros_like(idxs))

    return ret.to(x.dtype, bitcast=True), new_idxs