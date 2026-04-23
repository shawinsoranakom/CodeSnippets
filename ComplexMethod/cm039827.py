def _assert_all_finite(
    X, allow_nan=False, msg_dtype=None, estimator_name=None, input_name=""
):
    """Like assert_all_finite, but only for ndarray."""

    xp, is_array_api = get_namespace(X)

    if _get_config()["assume_finite"]:
        return

    X = xp.asarray(X)

    # for object dtype data, we only check for NaNs (GH-13254)
    if not is_array_api and X.dtype == np.dtype("object") and not allow_nan:
        if _object_dtype_isnan(X).any():
            raise ValueError("Input contains NaN")

    # We need only consider float arrays, hence can early return for all else.
    if not xp.isdtype(X.dtype, ("real floating", "complex floating")):
        return

    # First try an O(n) time, O(1) space solution for the common case that
    # everything is finite; fall back to O(n) space `np.isinf/isnan` or custom
    # Cython implementation to prevent false positives and provide a detailed
    # error message.
    with np.errstate(over="ignore"):
        first_pass_isfinite = xp.isfinite(xp.sum(X))
    if first_pass_isfinite:
        return

    _assert_all_finite_element_wise(
        X,
        xp=xp,
        allow_nan=allow_nan,
        msg_dtype=msg_dtype,
        estimator_name=estimator_name,
        input_name=input_name,
    )