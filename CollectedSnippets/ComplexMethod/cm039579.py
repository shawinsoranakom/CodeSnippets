def _solve_lbfgs(
    X,
    y,
    alpha,
    positive=True,
    max_iter=None,
    tol=1e-4,
    X_offset=None,
    X_scale=None,
    sample_weight_sqrt=None,
):
    """Solve ridge regression with LBFGS.

    The main purpose is fitting with forcing coefficients to be positive.
    For unconstrained ridge regression, there are faster dedicated solver methods.
    Note that with positive bounds on the coefficients, LBFGS seems faster
    than scipy.optimize.lsq_linear.
    """
    n_samples, n_features = X.shape

    options = {}
    if max_iter is not None:
        options["maxiter"] = max_iter
    config = {
        "method": "L-BFGS-B",
        "tol": tol,
        "jac": True,
        "options": options,
    }
    if positive:
        config["bounds"] = [(0, np.inf)] * n_features

    if X_offset is not None and X_scale is not None:
        X_offset_scale = X_offset / X_scale
    else:
        X_offset_scale = None

    if sample_weight_sqrt is None:
        sample_weight_sqrt = np.ones(X.shape[0], dtype=X.dtype)

    coefs = np.empty((y.shape[1], n_features), dtype=X.dtype)

    for i in range(y.shape[1]):
        x0 = np.zeros((n_features,))
        y_column = y[:, i]

        def func(w):
            residual = X.dot(w) - y_column
            if X_offset_scale is not None:
                residual -= sample_weight_sqrt * w.dot(X_offset_scale)
            f = 0.5 * residual.dot(residual) + 0.5 * alpha[i] * w.dot(w)
            grad = X.T @ residual + alpha[i] * w
            if X_offset_scale is not None:
                grad -= X_offset_scale * residual.dot(sample_weight_sqrt)

            return f, grad

        result = optimize.minimize(func, x0, **config)
        if not result["success"]:
            warnings.warn(
                (
                    "The lbfgs solver did not converge. Try increasing max_iter "
                    f"or tol. Currently: max_iter={max_iter} and tol={tol}"
                ),
                ConvergenceWarning,
            )
        coefs[i] = result["x"]

    return coefs