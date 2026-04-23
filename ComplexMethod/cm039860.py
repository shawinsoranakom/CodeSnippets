def _randomized_svd(
    M,
    n_components,
    *,
    n_oversamples=10,
    n_iter="auto",
    power_iteration_normalizer="auto",
    transpose="auto",
    flip_sign=True,
    random_state=None,
    svd_lapack_driver="gesdd",
):
    """Body of randomized_svd without input validation."""
    xp, is_array_api_compliant = get_namespace(M)

    if sparse.issparse(M) and M.format in ("lil", "dok"):
        warnings.warn(
            "Calculating SVD of a {} is expensive. "
            "CSR format is more efficient.".format(type(M).__name__),
            sparse.SparseEfficiencyWarning,
        )

    random_state = check_random_state(random_state)
    n_random = n_components + n_oversamples
    n_samples, n_features = M.shape

    if n_iter == "auto":
        # Checks if the number of iterations is explicitly specified
        # Adjust n_iter. 7 was found a good compromise for PCA. See #5299
        n_iter = 7 if n_components < 0.1 * min(M.shape) else 4

    if transpose == "auto":
        transpose = n_samples < n_features
    if transpose:
        # this implementation is a bit faster with smaller shape[1]
        M = M.T

    Q = _randomized_range_finder(
        M,
        size=n_random,
        n_iter=n_iter,
        power_iteration_normalizer=power_iteration_normalizer,
        random_state=random_state,
    )

    # project M to the (k + p) dimensional space using the basis vectors
    B = Q.T @ M

    # compute the SVD on the thin matrix: (k + p) wide
    if is_array_api_compliant:
        Uhat, s, Vt = xp.linalg.svd(B, full_matrices=False)
    else:
        # When array_api_dispatch is disabled, rely on scipy.linalg
        # instead of numpy.linalg to avoid introducing a behavior change w.r.t.
        # previous versions of scikit-learn.
        Uhat, s, Vt = linalg.svd(
            B, full_matrices=False, lapack_driver=svd_lapack_driver
        )
    del B
    U = Q @ Uhat

    if flip_sign:
        if not transpose:
            U, Vt = svd_flip(U, Vt)
        else:
            # In case of transpose u_based_decision=false
            # to actually flip based on u and not v.
            U, Vt = svd_flip(U, Vt, u_based_decision=False)

    if transpose:
        # transpose back the results according to the input convention
        return Vt[:n_components, :].T, s[:n_components], U[:, :n_components].T
    else:
        return U[:, :n_components], s[:n_components], Vt[:n_components, :]