def canonicalize_dim(rank: int, idx: int, wrap_scalar: bool = True) -> int:
    if rank < 0:
        msg = f"Rank cannot be negative but got {rank}"
        raise IndexError(msg)

    if rank == 0:
        if not wrap_scalar:
            msg = f"Dimension specified as {idx} but tensor has no dimensions"
            raise IndexError(msg)
        rank = 1

    if idx >= 0 and idx < rank:
        return idx

    if idx < 0:
        _idx = idx + rank
    else:
        _idx = idx

    if _idx < 0 or _idx >= rank:
        # Same error message as in aten/src/ATen/WrapDimUtils.h:49
        msg = f"Dimension out of range (expected to be in range of [{-rank}, {rank - 1}], but got {idx})"
        raise IndexError(msg)

    return _idx