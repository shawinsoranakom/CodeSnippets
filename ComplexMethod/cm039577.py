def _solve_sparse_cg(
    X,
    y,
    alpha,
    max_iter=None,
    tol=1e-4,
    verbose=0,
    X_offset=None,
    X_scale=None,
    sample_weight_sqrt=None,
):
    if sample_weight_sqrt is None:
        sample_weight_sqrt = np.ones(X.shape[0], dtype=X.dtype)

    n_samples, n_features = X.shape

    if X_offset is None or X_scale is None:
        X1 = sp_linalg.aslinearoperator(X)
    else:
        X_offset_scale = X_offset / X_scale
        X1 = _get_rescaled_operator(X, X_offset_scale, sample_weight_sqrt)

    coefs = np.empty((y.shape[1], n_features), dtype=X.dtype)

    if n_features > n_samples:

        def create_mv(curr_alpha):
            def _mv(x):
                return X1.matvec(X1.rmatvec(x)) + curr_alpha * x

            return _mv

    else:

        def create_mv(curr_alpha):
            def _mv(x):
                return X1.rmatvec(X1.matvec(x)) + curr_alpha * x

            return _mv

    for i in range(y.shape[1]):
        y_column = y[:, i]

        mv = create_mv(alpha[i])
        if n_features > n_samples:
            # kernel ridge
            # w = X.T * inv(X X^t + alpha*Id) y
            C = sp_linalg.LinearOperator(
                (n_samples, n_samples), matvec=mv, dtype=X.dtype
            )
            coef, info = _sparse_linalg_cg(C, y_column, rtol=tol)
            coefs[i] = X1.rmatvec(coef)
        else:
            # linear ridge
            # w = inv(X^t X + alpha*Id) * X.T y
            y_column = X1.rmatvec(y_column)
            C = sp_linalg.LinearOperator(
                (n_features, n_features), matvec=mv, dtype=X.dtype
            )
            coefs[i], info = _sparse_linalg_cg(C, y_column, maxiter=max_iter, rtol=tol)

        if info < 0:
            raise ValueError("Failed with error code %d" % info)

        if max_iter is None and info > 0 and verbose:
            warnings.warn(
                "sparse_cg did not converge after %d iterations." % info,
                ConvergenceWarning,
            )

    return coefs