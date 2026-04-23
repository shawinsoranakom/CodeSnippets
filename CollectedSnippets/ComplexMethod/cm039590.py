def _logistic_regression_path(
    X,
    y,
    *,
    classes,
    Cs=10,
    fit_intercept=True,
    max_iter=100,
    tol=1e-4,
    verbose=0,
    solver="lbfgs",
    coef=None,
    class_weight=None,
    dual=False,
    penalty="l2",
    intercept_scaling=1.0,
    random_state=None,
    check_input=True,
    max_squared_sum=None,
    sample_weight=None,
    l1_ratio=None,
    n_threads=1,
):
    """Compute a Logistic Regression model for a list of regularization
    parameters.

    This is an implementation that uses the result of the previous model
    to speed up computations along the set of solutions, making it faster
    than sequentially calling LogisticRegression for the different parameters.
    Note that there will be no speedup with liblinear solver, since it does
    not handle warm-starting.

    Read more in the :ref:`User Guide <logistic_regression>`.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Input data.

    y : array-like of shape (n_samples,) or (n_samples, n_targets)
        Input data, target values.

    classes : ndarray
        A list of class labels known to the classifier.

    Cs : int or array-like of shape (n_cs,), default=10
        List of values for the regularization parameter or integer specifying
        the number of regularization parameters that should be used. In this
        case, the parameters will be chosen in a logarithmic scale between
        1e-4 and 1e4.

    fit_intercept : bool, default=True
        Whether to fit an intercept for the model. In this case the shape of
        the returned array is (n_cs, n_features + 1).

    max_iter : int, default=100
        Maximum number of iterations for the solver.

    tol : float, default=1e-4
        Stopping criterion. For the newton-cg and lbfgs solvers, the iteration
        will stop when ``max{|g_i | i = 1, ..., n} <= tol``
        where ``g_i`` is the i-th component of the gradient.

    verbose : int, default=0
        For the liblinear and lbfgs solvers set verbose to any positive
        number for verbosity.

    solver : {'lbfgs', 'liblinear', 'newton-cg', 'newton-cholesky', 'sag', 'saga'}, \
            default='lbfgs'
        Numerical solver to use.

    coef : array-like of shape (n_classes, features + int(fit_intercept)) or \
            (1, n_features + int(fit_intercept)) or \
            (n_features + int(fit_intercept)), default=None
        Initialization value for coefficients of logistic regression.
        Useless for liblinear solver.

    class_weight : dict or 'balanced', default=None
        Weights associated with classes in the form ``{class_label: weight}``.
        If not given, all classes are supposed to have weight one.

        The "balanced" mode uses the values of y to automatically adjust
        weights inversely proportional to class frequencies in the input data
        as ``n_samples / (n_classes * np.bincount(y))``.

        Note that these weights will be multiplied with sample_weight (passed
        through the fit method) if sample_weight is specified.

    dual : bool, default=False
        Dual or primal formulation. Dual formulation is only implemented for
        l2 penalty with liblinear solver. Prefer dual=False when
        n_samples > n_features.

    penalty : {'l1', 'l2', 'elasticnet'}, default='l2'
        Used to specify the norm used in the penalization. The 'newton-cg',
        'sag' and 'lbfgs' solvers support only l2 penalties. 'elasticnet' is
        only supported by the 'saga' solver.

    intercept_scaling : float, default=1.
        Useful only when the solver `liblinear` is used
        and `self.fit_intercept` is set to `True`. In this case, `x` becomes
        `[x, self.intercept_scaling]`,
        i.e. a "synthetic" feature with constant value equal to
        `intercept_scaling` is appended to the instance vector.
        The intercept becomes
        ``intercept_scaling * synthetic_feature_weight``.

        .. note::
            The synthetic feature weight is subject to L1 or L2
            regularization as all other features.
            To lessen the effect of regularization on synthetic feature weight
            (and therefore on the intercept) `intercept_scaling` has to be increased.

    random_state : int, RandomState instance, default=None
        Used when ``solver`` == 'sag', 'saga' or 'liblinear' to shuffle the
        data. See :term:`Glossary <random_state>` for details.

    check_input : bool, default=True
        If False, the input arrays X and y will not be checked.

    max_squared_sum : float, default=None
        Maximum squared sum of X over samples. Used only in SAG solver.
        If None, it will be computed, going through all the samples.
        The value should be precomputed to speed up cross validation.

    sample_weight : array-like of shape (n_samples,), default=None
        Array of weights that are assigned to individual samples.
        If not provided, then each sample is given unit weight.

    l1_ratio : float, default=None
        The Elastic-Net mixing parameter, with ``0 <= l1_ratio <= 1``. Only
        used if ``penalty='elasticnet'``. Setting ``l1_ratio=0`` is equivalent
        to using ``penalty='l2'``, while setting ``l1_ratio=1`` is equivalent
        to using ``penalty='l1'``. For ``0 < l1_ratio <1``, the penalty is a
        combination of L1 and L2.

    n_threads : int, default=1
       Number of OpenMP threads to use.

    Returns
    -------
    coefs : ndarray of shape (n_cs, n_classes, n_features + int(fit_intercept)) or \
            (n_cs, n_features + int(fit_intercept))
        List of coefficients for the Logistic Regression model. If fit_intercept is set
        to True, then the last dimension will be n_features + 1, where the last item
        represents the intercept.
        For binary problems the second dimension in n_classes is dropped, i.e. the shape
        will be `(n_cs, n_features + int(fit_intercept))`.

    Cs : ndarray
        Grid of Cs used for cross-validation.

    n_iter : array of shape (n_cs,)
        Actual number of iteration for each C in Cs.

    Notes
    -----
    You might get slightly different results with the solver liblinear than
    with the others since this uses LIBLINEAR which penalizes the intercept.

    .. versionchanged:: 0.19
        The "copy" parameter was removed.
    """
    if isinstance(Cs, numbers.Integral):
        Cs = np.logspace(-4, 4, Cs)

    solver = _check_solver(solver, penalty, dual)
    xp, _, device_ = get_namespace_and_device(X)

    # Preprocessing.
    if check_input:
        X = check_array(
            X,
            accept_sparse="csr",
            dtype=[xp.float64, xp.float32],
            accept_large_sparse=solver not in ["liblinear", "sag", "saga"],
        )
        y = check_array(y, ensure_2d=False, dtype=None)
        check_consistent_length(X, y)

    if sample_weight is not None or class_weight is not None:
        sample_weight = _check_sample_weight(
            sample_weight, X, dtype=X.dtype, copy=True, ensure_same_device=True
        )

    n_samples, n_features = X.shape
    n_classes = classes.shape[0] if hasattr(classes, "shape") else len(classes)
    is_binary = n_classes == 2

    if solver == "liblinear" and not is_binary:
        raise ValueError(
            "The 'liblinear' solver does not support multiclass classification"
            " (n_classes >= 3). Either use another solver or wrap the "
            "estimator in a OneVsRestClassifier to keep applying a "
            "one-versus-rest scheme."
        )

    random_state = check_random_state(random_state)

    le = LabelEncoder().fit(classes)
    if class_weight is not None:
        class_weight_ = compute_class_weight(
            class_weight, classes=classes, y=y, sample_weight=sample_weight
        )
        class_weight_ = xp.asarray(
            class_weight_[le.transform(y)], dtype=X.dtype, device=device_
        )
        sample_weight *= class_weight_

    if is_binary:
        w0 = np.zeros(
            n_features + int(fit_intercept), dtype=_matching_numpy_dtype(X, xp=xp)
        )
        # classes[1] is the "positive label"
        mask = xp.asarray(y == classes[1], device=device_)
        y_bin = xp.ones(y.shape, dtype=X.dtype, device=device_)
        if solver == "liblinear":
            y_bin[~mask] = -1.0
        else:
            # HalfBinomialLoss, used for those solvers, represents y in [0, 1] instead
            # of in [-1, 1].
            y_bin[~mask] = 0.0
    else:
        # All solvers capable of a multinomial need LabelEncoder, not LabelBinarizer,
        # i.e. y as a 1d-array of integers. LabelEncoder also saves memory
        # compared to LabelBinarizer, especially when n_classes is large.
        Y_multi = xp.asarray(le.transform(y), dtype=X.dtype, device=device_)
        # It is important that w0 is F-contiguous.
        w0 = np.zeros(
            (size(classes), n_features + int(fit_intercept)),
            order="F",
            dtype=_matching_numpy_dtype(X, xp=xp),
        )

    # IMPORTANT NOTE:
    # All solvers relying on LinearModelLoss need to scale the penalty with n_samples
    # or the sum of sample weights because the implemented logistic regression
    # objective here is (unfortunately)
    #     C * sum(pointwise_loss) + penalty
    # instead of (as LinearModelLoss does)
    #     mean(pointwise_loss) + 1/C * penalty
    if solver in ["lbfgs", "newton-cg", "newton-cholesky"]:
        # This needs to be calculated after sample_weight is multiplied by
        # class_weight. It is even tested that passing class_weight is equivalent to
        # passing sample_weights according to class_weight.
        sw_sum = n_samples if sample_weight is None else float(xp.sum(sample_weight))

    if coef is not None:
        if is_binary:
            if coef.ndim == 1 and coef.shape[0] == n_features + int(fit_intercept):
                w0[:] = coef
            elif (
                coef.ndim == 2
                and coef.shape[0] == 1
                and coef.shape[1] == n_features + int(fit_intercept)
            ):
                w0[:] = coef[0]
            else:
                msg = (
                    f"Initialization coef is of shape {coef.shape}, expected shape "
                    f"{w0.shape} or (1, {w0.shape[0]})"
                )
                raise ValueError(msg)
        else:
            if (
                coef.ndim == 2
                and coef.shape[0] == n_classes
                and coef.shape[1] == n_features + int(fit_intercept)
            ):
                w0[:, : coef.shape[1]] = coef
            else:
                msg = (
                    f"Initialization coef is of shape {coef.shape}, expected shape "
                    f"{w0.shape}"
                )
                raise ValueError(msg)

    if is_binary:
        target = y_bin
        loss = LinearModelLoss(
            base_loss=(
                HalfBinomialLoss()
                if _is_numpy_namespace(xp)
                else HalfBinomialLossArrayAPI(xp=xp, device=device_)
            ),
            fit_intercept=fit_intercept,
        )
        if solver == "lbfgs":
            func = loss.loss_gradient
        elif solver == "newton-cg":
            func = loss.loss
            grad = loss.gradient
            hess = loss.gradient_hessian_product  # hess = [gradient, hessp]
        warm_start_sag = {"coef": np.expand_dims(w0, axis=1)}
    else:  # multinomial
        loss = LinearModelLoss(
            base_loss=(
                HalfMultinomialLoss(n_classes=size(classes))
                if _is_numpy_namespace(xp)
                else HalfMultinomialLossArrayAPI(
                    n_classes=size(classes), xp=xp, device=device_
                )
            ),
            fit_intercept=fit_intercept,
        )
        target = Y_multi
        if solver in ["lbfgs", "newton-cg", "newton-cholesky"]:
            # scipy.optimize.minimize and newton-cg accept only ravelled parameters,
            # i.e. 1d-arrays. LinearModelLoss expects classes to be contiguous and
            # reconstructs the 2d-array via w0.reshape((n_classes, -1), order="F").
            # As w0 is F-contiguous, ravel(order="F") also avoids a copy.
            w0 = w0.ravel(order="F")
        if solver == "lbfgs":
            func = loss.loss_gradient
        elif solver == "newton-cg":
            func = loss.loss
            grad = loss.gradient
            hess = loss.gradient_hessian_product  # hess = [gradient, hessp]
        warm_start_sag = {"coef": w0.T}

    coefs = list()
    n_iter = xp.zeros(len(Cs), dtype=xp.int32, device=device_)
    coefs_order = "C" if not _is_numpy_namespace(xp) else "K"
    for i, C in enumerate(Cs):
        if solver == "lbfgs":
            l2_reg_strength = 1.0 / (C * sw_sum)
            iprint = [-1, 50, 1, 100, 101][
                np.searchsorted(np.array([0, 1, 2, 3]), verbose)
            ]
            opt_res = optimize.minimize(
                func,
                w0,
                method="L-BFGS-B",
                jac=True,
                args=(X, target, sample_weight, l2_reg_strength, n_threads),
                options={
                    "maxiter": max_iter,
                    "maxls": 50,  # default is 20
                    "gtol": tol,
                    "ftol": 64 * np.finfo(float).eps,
                    **_get_additional_lbfgs_options_dict("iprint", iprint),
                },
            )
            n_iter_i = _check_optimize_result(
                solver,
                opt_res,
                max_iter,
                extra_warning_msg=_LOGISTIC_SOLVER_CONVERGENCE_MSG,
            )
            w0, loss = opt_res.x, opt_res.fun
        elif solver == "newton-cg":
            l2_reg_strength = 1.0 / (C * sw_sum)
            args = (X, target, sample_weight, l2_reg_strength, n_threads)
            w0, n_iter_i = _newton_cg(
                grad_hess=hess,
                func=func,
                grad=grad,
                x0=w0,
                args=args,
                maxiter=max_iter,
                tol=tol,
                verbose=verbose,
            )
        elif solver == "newton-cholesky":
            l2_reg_strength = 1.0 / (C * sw_sum)
            sol = NewtonCholeskySolver(
                coef=w0,
                linear_loss=loss,
                l2_reg_strength=l2_reg_strength,
                tol=tol,
                max_iter=max_iter,
                n_threads=n_threads,
                verbose=verbose,
            )
            w0 = sol.solve(X=X, y=target, sample_weight=sample_weight)
            n_iter_i = sol.iteration
        elif solver == "liblinear":
            coef_, intercept_, n_iter_i = _fit_liblinear(
                X,
                target,
                C,
                fit_intercept,
                intercept_scaling,
                None,
                penalty,
                dual,
                verbose,
                max_iter,
                tol,
                random_state,
                sample_weight=sample_weight,
            )
            if fit_intercept:
                w0 = np.concatenate([coef_.ravel(), intercept_])
            else:
                w0 = coef_.ravel()
            # n_iter_i is an array for each class. However, `target` is always encoded
            # in {-1, 1}, so we only take the first element of n_iter_i.
            n_iter_i = n_iter_i.item()

        elif solver in ["sag", "saga"]:
            if is_binary:
                loss = "log"
            else:
                target = target.astype(X.dtype, copy=False)
                loss = "multinomial"
            # alpha is for L2-norm, beta is for L1-norm
            if penalty == "l1":
                alpha = 0.0
                beta = 1.0 / C
            elif penalty == "l2":
                alpha = 1.0 / C
                beta = 0.0
            else:  # Elastic-Net penalty
                alpha = (1.0 / C) * (1 - l1_ratio)
                beta = (1.0 / C) * l1_ratio

            w0, n_iter_i, warm_start_sag = sag_solver(
                X,
                target,
                sample_weight,
                loss,
                alpha,
                beta,
                max_iter,
                tol,
                verbose,
                random_state,
                False,
                max_squared_sum,
                warm_start_sag,
                is_saga=(solver == "saga"),
            )

        else:
            msg = (
                "solver must be one of {'lbfgs', 'liblinear', 'newton-cg', "
                "'newton-cholesky', 'sag', 'saga'}, "
                f"got '{solver}' instead."
            )
            raise ValueError(msg)

        if is_binary:
            coefs.append(
                xp.asarray(w0.copy(order=coefs_order), dtype=X.dtype, device=device_)
            )
        else:
            if solver in ["lbfgs", "newton-cg", "newton-cholesky"]:
                multi_w0 = np.reshape(w0, (n_classes, -1), order="F")
            else:
                multi_w0 = w0
            coefs.append(
                xp.asarray(
                    multi_w0.copy(order=coefs_order), dtype=X.dtype, device=device_
                )
            )

        n_iter[i] = n_iter_i

    return xp.stack(coefs), xp.asarray(Cs, device=device_), n_iter