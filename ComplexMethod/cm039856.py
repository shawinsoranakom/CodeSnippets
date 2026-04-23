def _unique_np(values, return_inverse=False, return_counts=False):
    """Helper function to find unique values for numpy arrays that correctly
    accounts for nans. See `_unique` documentation for details."""
    xp, _ = get_namespace(values)

    inverse, counts = None, None

    if return_inverse and return_counts:
        uniques, _, inverse, counts = xp.unique_all(values)
    elif return_inverse:
        uniques, inverse = xp.unique_inverse(values)
    elif return_counts:
        uniques, counts = xp.unique_counts(values)
    else:
        uniques = xp.unique_values(values)

    # np.unique will have duplicate missing values at the end of `uniques`
    # here we clip the nans and remove it from uniques
    if uniques.size and is_scalar_nan(uniques[-1]):
        nan_idx = xp.searchsorted(uniques, xp.nan)
        uniques = uniques[: nan_idx + 1]
        if return_inverse:
            inverse[inverse > nan_idx] = nan_idx

        if return_counts:
            counts[nan_idx] = xp.sum(counts[nan_idx:])
            counts = counts[: nan_idx + 1]

    ret = (uniques,)

    if return_inverse:
        ret += (inverse,)

    if return_counts:
        ret += (counts,)

    return ret[0] if len(ret) == 1 else ret