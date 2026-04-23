def _ridge_regression(
    X,
    y,
    alpha,
    sample_weight=None,
    solver="auto",
    max_iter=None,
    tol=1e-4,
    verbose=0,
    positive=False,
    random_state=None,
    return_n_iter=False,
    return_intercept=False,
    return_solver=False,
    X_scale=None,
    X_offset=None,
    check_input=True,
    fit_intercept=False,
):
    xp, is_array_api_compliant, device_ = get_namespace_and_device(
        X, y, sample_weight, X_scale, X_offset
    )
    is_numpy_namespace = _is_numpy_namespace(xp)
    X_is_sparse = sparse.issparse(X)

    has_sw = sample_weight is not None

    solver = resolve_solver(solver, positive, return_intercept, X_is_sparse, xp)

    if is_numpy_namespace and not X_is_sparse:
        X = np.asarray(X)

    if not is_numpy_namespace and solver != "svd":
        raise ValueError(
            f"Array API dispatch to namespace {xp.__name__} only supports "
            f"solver 'svd'. Got '{solver}'."
        )

    if positive and solver != "lbfgs":
        raise ValueError(
            "When positive=True, only 'lbfgs' solver can be used. "
            f"Please change solver {solver} to 'lbfgs' "
            "or set positive=False."
        )

    if solver == "lbfgs" and not positive:
        raise ValueError(
            "'lbfgs' solver can be used only when positive=True. "
            "Please use another solver."
        )

    if return_intercept and solver != "sag":
        raise ValueError(
            "In Ridge, only 'sag' solver can directly fit the "
            "intercept. Please change solver to 'sag' or set "
            "return_intercept=False."
        )

    if check_input:
        _dtype = [xp.float64, xp.float32]
        _accept_sparse = _get_valid_accept_sparse(X_is_sparse, solver)
        X = check_array(X, accept_sparse=_accept_sparse, dtype=_dtype, order="C")
        y = check_array(y, dtype=X.dtype, ensure_2d=False, order=None)
    check_consistent_length(X, y)

    n_samples, n_features = X.shape

    if y.ndim > 2:
        raise ValueError("Target y has the wrong shape %s" % str(y.shape))

    if y.ndim == 1:
        y = xp.reshape(y, (-1, 1))

    n_samples_, n_targets = y.shape

    if n_samples != n_samples_:
        raise ValueError(
            "Number of samples in X and y does not correspond: %d != %d"
            % (n_samples, n_samples_)
        )

    if has_sw:
        sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        if solver not in ["sag", "saga"]:
            # SAG supports sample_weight directly. For other solvers,
            # we implement sample_weight via a simple rescaling.
            X, y, sample_weight_sqrt = _rescale_data(X, y, sample_weight)

    # Some callers of this method might pass alpha as single
    # element array which already has been validated.
    if alpha is not None and not isinstance(alpha, type(xp.asarray([0.0]))):
        alpha = check_scalar(
            alpha,
            "alpha",
            target_type=numbers.Real,
            min_val=0.0,
            include_boundaries="left",
        )

    # There should be either 1 or n_targets penalties
    alpha = _ravel(xp.asarray(alpha, device=device_, dtype=X.dtype), xp=xp)
    if alpha.shape[0] not in [1, n_targets]:
        raise ValueError(
            "Number of targets and number of penalties do not correspond: %d != %d"
            % (alpha.shape[0], n_targets)
        )

    if alpha.shape[0] == 1 and n_targets > 1:
        alpha = xp.full(
            shape=(n_targets,),
            fill_value=float(alpha[0]),
            dtype=alpha.dtype,
            device=device_,
        )

    n_iter = None
    if solver == "sparse_cg":
        coef = _solve_sparse_cg(
            X,
            y,
            alpha,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose,
            X_offset=X_offset,
            X_scale=X_scale,
            sample_weight_sqrt=sample_weight_sqrt if has_sw else None,
        )

    elif solver == "lsqr":
        coef, n_iter = _solve_lsqr(
            X,
            y,
            alpha=alpha,
            fit_intercept=fit_intercept,
            max_iter=max_iter,
            tol=tol,
            X_offset=X_offset,
            X_scale=X_scale,
            sample_weight_sqrt=sample_weight_sqrt if has_sw else None,
        )

    elif solver == "cholesky":
        if n_features > n_samples:
            K = safe_sparse_dot(X, X.T, dense_output=True)
            try:
                dual_coef = _solve_cholesky_kernel(K, y, alpha)

                coef = safe_sparse_dot(X.T, dual_coef, dense_output=True).T
            except linalg.LinAlgError:
                # use SVD solver if matrix is singular
                solver = "svd"
        else:
            try:
                coef = _solve_cholesky(X, y, alpha)
            except linalg.LinAlgError:
                # use SVD solver if matrix is singular
                solver = "svd"

    elif solver in ["sag", "saga"]:
        # precompute max_squared_sum for all targets
        max_squared_sum = row_norms(X, squared=True).max()

        coef = np.empty((y.shape[1], n_features), dtype=X.dtype)
        n_iter = np.empty(y.shape[1], dtype=np.int32)
        intercept = np.zeros((y.shape[1],), dtype=X.dtype)
        for i, (alpha_i, target) in enumerate(zip(alpha, y.T)):
            init = {
                "coef": np.zeros((n_features + int(return_intercept), 1), dtype=X.dtype)
            }
            coef_, n_iter_, _ = sag_solver(
                X,
                target.ravel(),
                sample_weight,
                "squared",
                alpha_i,
                0,
                max_iter,
                tol,
                verbose,
                random_state,
                False,
                max_squared_sum,
                init,
                is_saga=solver == "saga",
            )
            if return_intercept:
                coef[i] = coef_[:-1]
                intercept[i] = coef_[-1]
            else:
                coef[i] = coef_
            n_iter[i] = n_iter_

        if intercept.shape[0] == 1:
            intercept = intercept[0]

    elif solver == "lbfgs":
        coef = _solve_lbfgs(
            X,
            y,
            alpha,
            positive=positive,
            tol=tol,
            max_iter=max_iter,
            X_offset=X_offset,
            X_scale=X_scale,
            sample_weight_sqrt=sample_weight_sqrt if has_sw else None,
        )

    if solver == "svd":
        if X_is_sparse:
            raise TypeError("SVD solver does not support sparse inputs currently")
        coef = _solve_svd(X, y, alpha, xp)

    if n_targets == 1:
        coef = _ravel(coef)

    coef = xp.asarray(coef)

    if return_n_iter and return_intercept:
        res = coef, n_iter, intercept
    elif return_intercept:
        res = coef, intercept
    elif return_n_iter:
        res = coef, n_iter
    else:
        res = coef

    return (*res, solver) if return_solver else res