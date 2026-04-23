def histogramdd(
    sample,
    bins=10,
    range: ArrayLike | None = None,
    normed=None,
    weights: ArrayLike | None = None,
    density=None,
):
    # have to normalize manually because `sample` interpretation differs
    # for a list of lists and a 2D array
    if normed is not None:
        raise ValueError("normed argument is deprecated, use density= instead")

    from ._normalizations import normalize_array_like, normalize_seq_array_like

    if isinstance(sample, (list, tuple)):
        sample = normalize_array_like(sample).T
    else:
        sample = normalize_array_like(sample)

    sample = torch.atleast_2d(sample)

    if not (sample.dtype.is_floating_point or sample.dtype.is_complex):
        sample = sample.double()

    # bins is either an int, or a sequence of ints or a sequence of arrays
    bins_is_array = not (
        isinstance(bins, int) or builtins.all(isinstance(b, int) for b in bins)
    )
    if bins_is_array:
        bins = normalize_seq_array_like(bins)
        bins_dtypes = [b.dtype for b in bins]
        bins = [_util.cast_if_needed(b, sample.dtype) for b in bins]

    if range is not None:
        range = range.flatten().tolist()

    if weights is not None:
        # range=... is required : interleave min and max values per dimension
        mm = sample.aminmax(dim=0)
        range = torch.cat(mm).reshape(2, -1).T.flatten()
        range = tuple(range.tolist())
        weights = _util.cast_if_needed(weights, sample.dtype)
        w_kwd = {"weight": weights}
    else:
        w_kwd = {}

    h, b = torch.histogramdd(sample, bins, range, density=bool(density), **w_kwd)

    if bins_is_array:
        b = [_util.cast_if_needed(bb, dtyp) for bb, dtyp in zip(b, bins_dtypes)]

    return h, b