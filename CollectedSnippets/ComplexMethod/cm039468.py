def _graphical_lasso(
    emp_cov,
    alpha,
    *,
    cov_init=None,
    mode="cd",
    tol=1e-4,
    enet_tol=1e-4,
    max_iter=100,
    verbose=False,
    eps=np.finfo(np.float64).eps,
):
    _, n_features = emp_cov.shape
    if alpha == 0:
        # Early return without regularization
        precision_ = linalg.inv(emp_cov)
        cost = -2.0 * log_likelihood(emp_cov, precision_)
        cost += n_features * np.log(2 * np.pi)
        d_gap = np.sum(emp_cov * precision_) - n_features
        return emp_cov, precision_, (cost, d_gap), 0

    if cov_init is None:
        covariance_ = emp_cov.copy()
    else:
        covariance_ = cov_init.copy()
    # As a trivial regularization (Tikhonov like), we scale down the
    # off-diagonal coefficients of our starting point: This is needed, as
    # in the cross-validation the cov_init can easily be
    # ill-conditioned, and the CV loop blows. Beside, this takes
    # conservative stand-point on the initial conditions, and it tends to
    # make the convergence go faster.
    covariance_ *= 0.95
    diagonal = emp_cov.flat[:: n_features + 1]
    covariance_.flat[:: n_features + 1] = diagonal
    precision_ = linalg.pinvh(covariance_)

    indices = np.arange(n_features)
    i = 0  # initialize the counter to be robust to `max_iter=0`
    costs = list()
    # The different l1 regression solver have different numerical errors
    if mode == "cd":
        errors = dict(over="raise", invalid="ignore")
    else:
        errors = dict(invalid="raise")
    try:
        # be robust to the max_iter=0 edge case, see:
        # https://github.com/scikit-learn/scikit-learn/issues/4134
        d_gap = np.inf
        # set a sub_covariance buffer
        sub_covariance = np.copy(covariance_[1:, 1:], order="C")
        for i in range(max_iter):
            for idx in range(n_features):
                # To keep the contiguous matrix `sub_covariance` equal to
                # covariance_[indices != idx].T[indices != idx]
                # we only need to update 1 column and 1 line when idx changes
                if idx > 0:
                    di = idx - 1
                    sub_covariance[di] = covariance_[di][indices != idx]
                    sub_covariance[:, di] = covariance_[:, di][indices != idx]
                else:
                    sub_covariance[:] = covariance_[1:, 1:]
                row = emp_cov[idx, indices != idx]
                with np.errstate(**errors):
                    if mode == "cd":
                        # Use coordinate descent
                        coefs = -(
                            precision_[indices != idx, idx]
                            / (precision_[idx, idx] + 1000 * eps)
                        )
                        coefs, _, _, _ = cd_fast.enet_coordinate_descent_gram(
                            w=coefs,
                            alpha=alpha,
                            beta=0,
                            Q=sub_covariance,
                            q=row,
                            y=row,
                            # TODO: It is not ideal that the max_iter of the outer
                            # solver (graphical lasso) is coupled with the max_iter of
                            # the inner solver (CD). Ideally, CD has its own parameter
                            # enet_max_iter (like enet_tol). A minimum of 20 is rather
                            # arbitrary, but not unreasonable.
                            max_iter=max(20, max_iter),
                            tol=enet_tol,
                            rng=check_random_state(None),
                            random=False,
                            positive=False,
                            do_screening=True,
                        )
                    else:  # mode == "lars"
                        _, _, coefs = lars_path_gram(
                            Xy=row,
                            Gram=sub_covariance,
                            n_samples=row.size,
                            alpha_min=alpha / (n_features - 1),
                            copy_Gram=True,
                            eps=eps,
                            method="lars",
                            return_path=False,
                        )
                # Update the precision matrix
                precision_[idx, idx] = 1.0 / (
                    covariance_[idx, idx]
                    - np.dot(covariance_[indices != idx, idx], coefs)
                )
                precision_[indices != idx, idx] = -precision_[idx, idx] * coefs
                precision_[idx, indices != idx] = -precision_[idx, idx] * coefs
                coefs = np.dot(sub_covariance, coefs)
                covariance_[idx, indices != idx] = coefs
                covariance_[indices != idx, idx] = coefs
            if not np.isfinite(precision_.sum()):
                raise FloatingPointError(
                    "The system is too ill-conditioned for this solver"
                )
            d_gap = _dual_gap(emp_cov, precision_, alpha)
            cost = _objective(emp_cov, precision_, alpha)
            if verbose:
                print(
                    "[graphical_lasso] Iteration % 3i, cost % 3.2e, dual gap %.3e"
                    % (i, cost, d_gap)
                )
            costs.append((cost, d_gap))
            if np.abs(d_gap) < tol:
                break
            if not np.isfinite(cost) and i > 0:
                raise FloatingPointError(
                    "Non SPD result: the system is too ill-conditioned for this solver"
                )
        else:
            warnings.warn(
                "graphical_lasso: did not converge after %i iteration: dual gap: %.3e"
                % (max_iter, d_gap),
                ConvergenceWarning,
            )
    except FloatingPointError as e:
        e.args = (e.args[0] + ". The system is too ill-conditioned for this solver",)
        raise e

    return covariance_, precision_, costs, i + 1