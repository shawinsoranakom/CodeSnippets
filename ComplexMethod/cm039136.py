def _sparse_encode(
    X,
    dictionary,
    *,
    gram=None,
    cov=None,
    algorithm="lasso_lars",
    n_nonzero_coefs=None,
    alpha=None,
    copy_cov=True,
    init=None,
    max_iter=1000,
    n_jobs=None,
    verbose=0,
    positive=False,
):
    """Sparse coding without input/parameter validation."""

    n_samples, n_features = X.shape
    n_components = dictionary.shape[0]

    if algorithm in ("lars", "omp"):
        regularization = n_nonzero_coefs
        if regularization is None:
            regularization = min(max(n_features / 10, 1), n_components)
    else:
        regularization = alpha
        if regularization is None:
            regularization = 1.0

    if gram is None and algorithm != "threshold":
        gram = np.dot(dictionary, dictionary.T).astype(X.dtype, copy=False)

    if cov is None and algorithm != "lasso_cd":
        copy_cov = False
        cov = np.dot(dictionary, X.T)

    if effective_n_jobs(n_jobs) == 1 or algorithm == "threshold":
        code = _sparse_encode_precomputed(
            X,
            dictionary,
            gram=gram,
            cov=cov,
            algorithm=algorithm,
            regularization=regularization,
            copy_cov=copy_cov,
            init=init,
            max_iter=max_iter,
            verbose=verbose,
            positive=positive,
        )
        return code

    # Enter parallel code block
    n_samples = X.shape[0]
    n_components = dictionary.shape[0]
    code = np.empty((n_samples, n_components))
    slices = list(gen_even_slices(n_samples, effective_n_jobs(n_jobs)))

    code_views = Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(_sparse_encode_precomputed)(
            X[this_slice],
            dictionary,
            gram=gram,
            cov=cov[:, this_slice] if cov is not None else None,
            algorithm=algorithm,
            regularization=regularization,
            copy_cov=copy_cov,
            init=init[this_slice] if init is not None else None,
            max_iter=max_iter,
            verbose=verbose,
            positive=positive,
        )
        for this_slice in slices
    )
    for this_slice, this_view in zip(slices, code_views):
        code[this_slice] = this_view
    return code