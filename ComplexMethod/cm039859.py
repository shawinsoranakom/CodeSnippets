def _randomized_range_finder(
    A, *, size, n_iter, power_iteration_normalizer="auto", random_state=None
):
    """Body of randomized_range_finder without input validation."""
    xp, is_array_api_compliant = get_namespace(A)
    random_state = check_random_state(random_state)

    # Generating normal random vectors with shape: (A.shape[1], size)
    # XXX: generate random number directly from xp if it's possible
    # one day.
    Q = xp.asarray(random_state.normal(size=(A.shape[1], size)))
    if hasattr(A, "dtype") and xp.isdtype(A.dtype, kind="real floating"):
        # Use float32 computation and components if A has a float32 dtype.
        Q = xp.astype(Q, A.dtype, copy=False)

    # Move Q to device if needed only after converting to float32 if needed to
    # avoid allocating unnecessary memory on the device.

    # Note: we cannot combine the astype and to_device operations in one go
    # using xp.asarray(..., dtype=dtype, device=device) because downcasting
    # from float64 to float32 in asarray might not always be accepted as only
    # casts following type promotion rules are guarateed to work.
    # https://github.com/data-apis/array-api/issues/647
    if is_array_api_compliant:
        Q = xp.asarray(Q, device=device(A))

    # Deal with "auto" mode
    if power_iteration_normalizer == "auto":
        if n_iter <= 2:
            power_iteration_normalizer = "none"
        elif is_array_api_compliant:
            # XXX: https://github.com/data-apis/array-api/issues/627
            warnings.warn(
                "Array API does not support LU factorization, falling back to QR"
                " instead. Set `power_iteration_normalizer='QR'` explicitly to silence"
                " this warning."
            )
            power_iteration_normalizer = "QR"
        else:
            power_iteration_normalizer = "LU"
    elif power_iteration_normalizer == "LU" and is_array_api_compliant:
        raise ValueError(
            "Array API does not support LU factorization. Set "
            "`power_iteration_normalizer='QR'` instead."
        )

    if is_array_api_compliant:
        qr_normalizer = partial(xp.linalg.qr, mode="reduced")
    else:
        # Use scipy.linalg instead of numpy.linalg when not explicitly
        # using the Array API.
        qr_normalizer = partial(linalg.qr, mode="economic", check_finite=False)

    if power_iteration_normalizer == "QR":
        normalizer = qr_normalizer
    elif power_iteration_normalizer == "LU":
        normalizer = partial(linalg.lu, permute_l=True, check_finite=False)
    else:
        normalizer = lambda x: (x, None)

    # Perform power iterations with Q to further 'imprint' the top
    # singular vectors of A in Q
    for _ in range(n_iter):
        Q, _ = normalizer(A @ Q)
        Q, _ = normalizer(A.T @ Q)

    # Sample the range of A using by linear projection of Q
    # Extract an orthonormal basis
    Q, _ = qr_normalizer(A @ Q)

    return Q