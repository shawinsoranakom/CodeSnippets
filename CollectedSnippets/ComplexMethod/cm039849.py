def _safely_cast_index_arrays(A, idx_dtype=np.int32, msg=""):
    """Safely cast sparse array indices to `idx_dtype`.

    Check the shape of `A` to determine if it is safe to cast its index
    arrays to dtype `idx_dtype`. If any dimension in shape is larger than
    fits in the dtype, casting is unsafe so raise ``ValueError``.
    If safe, cast the index arrays to `idx_dtype` and return the result
    without changing the input `A`. The caller can assign results to `A`
    attributes if desired or use the recast index arrays directly.

    Unless downcasting is needed, the original index arrays are returned.
    You can test e.g. ``A.indptr is new_indptr`` to see if downcasting occurred.

    See SciPy: scipy.sparse._sputils.py for more info on safely_cast_index_arrays()
    """
    max_value = np.iinfo(idx_dtype).max

    if A.format in ("csc", "csr"):
        if A.indptr[-1] > max_value:
            raise ValueError(f"indptr values too large for {msg}")
        # check shape vs dtype
        if max(*A.shape) > max_value:
            if (A.indices > max_value).any():
                raise ValueError(f"indices values too large for {msg}")

        indices = A.indices.astype(idx_dtype, copy=False)
        indptr = A.indptr.astype(idx_dtype, copy=False)
        return indices, indptr

    elif A.format == "coo":
        coords = getattr(A, "coords", None)
        if coords is None:
            coords = getattr(A, "indices", None)
            if coords is None:
                coords = (A.row, A.col)
        if max(*A.shape) > max_value:
            if any((co > max_value).any() for co in coords):
                raise ValueError(f"coords values too large for {msg}")
        return tuple(co.astype(idx_dtype, copy=False) for co in coords)

    elif A.format == "dia":
        if max(*A.shape) > max_value:
            if (A.offsets > max_value).any():
                raise ValueError(f"offsets values too large for {msg}")
        offsets = A.offsets.astype(idx_dtype, copy=False)
        return offsets

    elif A.format == "bsr":
        R, C = A.blocksize
        if A.indptr[-1] * R > max_value:
            raise ValueError("indptr values too large for {msg}")
        if max(*A.shape) > max_value:
            if (A.indices * C > max_value).any():
                raise ValueError(f"indices values too large for {msg}")
        indices = A.indices.astype(idx_dtype, copy=False)
        indptr = A.indptr.astype(idx_dtype, copy=False)
        return indices, indptr