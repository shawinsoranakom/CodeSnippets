def _in1d(ar1, ar2, xp, assume_unique=False, invert=False):
    """Checks whether each element of an array is also present in a
    second array.

    Returns a boolean array the same length as `ar1` that is True
    where an element of `ar1` is in `ar2` and False otherwise.

    This function has been adapted using the original implementation
    present in numpy:
    https://github.com/numpy/numpy/blob/v1.26.0/numpy/lib/arraysetops.py#L524-L758
    """
    xp, _ = get_namespace(ar1, ar2, xp=xp)

    # This code is run to make the code significantly faster
    if ar2.shape[0] < 10 * ar1.shape[0] ** 0.145:
        if invert:
            mask = xp.ones(ar1.shape[0], dtype=xp.bool, device=device(ar1))
            for a in ar2:
                mask &= ar1 != a
        else:
            mask = xp.zeros(ar1.shape[0], dtype=xp.bool, device=device(ar1))
            for a in ar2:
                mask |= ar1 == a
        return mask

    if not assume_unique:
        ar1, rev_idx = xp.unique_inverse(ar1)
        ar2 = xp.unique_values(ar2)

    ar = xp.concat((ar1, ar2))
    device_ = device(ar)
    # We need this to be a stable sort.
    order = xp.argsort(ar, stable=True)
    reverse_order = xp.argsort(order, stable=True)
    sar = xp.take(ar, order, axis=0)
    if size(sar) >= 1:
        bool_ar = sar[1:] != sar[:-1] if invert else sar[1:] == sar[:-1]
    else:
        # indexing undefined in standard when sar is empty
        bool_ar = xp.asarray([False]) if invert else xp.asarray([True])
    flag = xp.concat((bool_ar, xp.asarray([invert], device=device_)))
    ret = xp.take(flag, reverse_order, axis=0)

    if assume_unique:
        return ret[: ar1.shape[0]]
    else:
        return xp.take(ret, rev_idx, axis=0)