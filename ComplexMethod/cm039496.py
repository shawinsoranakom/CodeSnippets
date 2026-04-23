def _euclidean_distances(X, Y, X_norm_squared=None, Y_norm_squared=None, squared=False):
    """Computational part of euclidean_distances

    Assumes inputs are already checked.

    If norms are passed as float32, they are unused. If arrays are passed as
    float32, norms needs to be recomputed on upcast chunks.
    TODO: use a float64 accumulator in row_norms to avoid the latter.
    """
    xp, _, device_ = get_namespace_and_device(X, Y)
    if X_norm_squared is not None and X_norm_squared.dtype != xp.float32:
        XX = xp.reshape(X_norm_squared, (-1, 1))
    elif X.dtype != xp.float32:
        XX = row_norms(X, squared=True)[:, None]
    else:
        XX = None

    if Y is X:
        YY = None if XX is None else XX.T
    else:
        if Y_norm_squared is not None and Y_norm_squared.dtype != xp.float32:
            YY = xp.reshape(Y_norm_squared, (1, -1))
        elif Y.dtype != xp.float32:
            YY = row_norms(Y, squared=True)[None, :]
        else:
            YY = None

    if X.dtype == xp.float32 or Y.dtype == xp.float32:
        # To minimize precision issues with float32, we compute the distance
        # matrix on chunks of X and Y upcast to float64
        distances = _euclidean_distances_upcast(X, XX, Y, YY)
    else:
        # if dtype is already float64, no need to chunk and upcast
        distances = -2 * safe_sparse_dot(X, Y.T, dense_output=True)
        distances += XX
        distances += YY

    xp_zero = xp.asarray(0, device=device_, dtype=distances.dtype)
    distances = _modify_in_place_if_numpy(
        xp, xp.maximum, distances, xp_zero, out=distances
    )

    # Ensure that distances between vectors and themselves are set to 0.0.
    # This may not be the case due to floating point rounding errors.
    if X is Y:
        _fill_diagonal(distances, 0, xp=xp)

    if squared:
        return distances

    distances = _modify_in_place_if_numpy(xp, xp.sqrt, distances, out=distances)
    return distances