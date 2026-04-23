def enet_path(
    X,
    y,
    *,
    l1_ratio=0.5,
    eps=1e-3,
    n_alphas=100,
    alphas=None,
    precompute="auto",
    Xy=None,
    copy_X=True,
    coef_init=None,
    verbose=False,
    return_n_iter=False,
    positive=False,
    check_input=True,
    **params,
):
    """Compute elastic net path with coordinate descent.

    The elastic net optimization function varies for mono and multi-outputs.

    For mono-output tasks it is::

        1 / (2 * n_samples) * ||y - Xw||^2_2
        + alpha * l1_ratio * ||w||_1
        + 0.5 * alpha * (1 - l1_ratio) * ||w||^2_2

    For multi-output tasks it is::

        1 / (2 * n_samples) * ||Y - XW||_Fro^2
        + alpha * l1_ratio * ||W||_21
        + 0.5 * alpha * (1 - l1_ratio) * ||W||_Fro^2

    Where::

        ||W||_21 = \\sum_i \\sqrt{\\sum_j w_{ij}^2}

    i.e. the sum of L2-norm of each row (task) (i=feature, j=task)

    Read more in the :ref:`User Guide <elastic_net>`.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Training data. Pass directly as Fortran-contiguous data to avoid
        unnecessary memory duplication. If ``y`` is mono-output then ``X``
        can be sparse.

    y : {array-like, sparse matrix} of shape (n_samples,) or \
        (n_samples, n_targets)
        Target values.

    l1_ratio : float, default=0.5
        Number between 0 and 1 passed to elastic net (scaling between
        l1 and l2 penalties). ``l1_ratio=1`` corresponds to the Lasso.

    eps : float, default=1e-3
        Length of the path. ``eps=1e-3`` means that
        ``alpha_min / alpha_max = 1e-3``.

    n_alphas : int, default=100
        Number of alphas along the regularization path.

    alphas : array-like, default=None
        List of alphas where to compute the models.
        If None alphas are set automatically.

    precompute : 'auto', bool or array-like of shape \
            (n_features, n_features), default='auto'
        Whether to use a precomputed Gram matrix to speed up
        calculations. If set to ``'auto'`` let us decide. The Gram
        matrix can also be passed as argument.

    Xy : array-like of shape (n_features,) or (n_features, n_targets),\
         default=None
        Xy = np.dot(X.T, y) that can be precomputed. It is useful
        only when the Gram matrix is precomputed.

    copy_X : bool, default=True
        If ``True``, X will be copied; else, it may be overwritten.

    coef_init : array-like of shape (n_features, ), default=None
        The initial values of the coefficients.

    verbose : bool or int, default=False
        Amount of verbosity.

    return_n_iter : bool, default=False
        Whether to return the number of iterations or not.

    positive : bool, default=False
        If set to True, forces coefficients to be positive.
        (Only allowed when ``y.ndim == 1``).

    check_input : bool, default=True
        If set to False, the input validation checks are skipped (including the
        Gram matrix when provided). It is assumed that they are handled
        by the caller.

    **params : kwargs
        Keyword arguments passed to the coordinate descent solver.

    Returns
    -------
    alphas : ndarray of shape (n_alphas,)
        The alphas along the path where models are computed.

    coefs : ndarray of shape (n_features, n_alphas) or \
            (n_targets, n_features, n_alphas)
        Coefficients along the path.

    dual_gaps : ndarray of shape (n_alphas,)
        The dual gaps at the end of the optimization for each alpha.

    n_iters : list of int
        The number of iterations taken by the coordinate descent optimizer to
        reach the specified tolerance for each alpha.
        (Is returned when ``return_n_iter`` is set to True).

    See Also
    --------
    MultiTaskElasticNet : Multi-task ElasticNet model trained with L1/L2 mixed-norm \
    as regularizer.
    MultiTaskElasticNetCV : Multi-task L1/L2 ElasticNet with built-in cross-validation.
    ElasticNet : Linear regression with combined L1 and L2 priors as regularizer.
    ElasticNetCV : Elastic Net model with iterative fitting along a regularization path.

    Notes
    -----
    For an example, see
    :ref:`examples/linear_model/plot_lasso_lasso_lars_elasticnet_path.py
    <sphx_glr_auto_examples_linear_model_plot_lasso_lasso_lars_elasticnet_path.py>`.

    The underlying coordinate descent solver uses gap safe screening rules to speedup
    fitting time, see :ref:`User Guide on coordinate descent <coordinate_descent>`.

    Examples
    --------
    >>> from sklearn.linear_model import enet_path
    >>> from sklearn.datasets import make_regression
    >>> X, y, true_coef = make_regression(
    ...    n_samples=100, n_features=5, n_informative=2, coef=True, random_state=0
    ... )
    >>> true_coef
    array([ 0.        ,  0.        ,  0.        , 97.9, 45.7])
    >>> alphas, estimated_coef, _ = enet_path(X, y, n_alphas=3)
    >>> alphas.shape
    (3,)
    >>> estimated_coef
     array([[ 0.,  0.787,  0.568],
            [ 0.,  1.120,  0.620],
            [-0., -2.129, -1.128],
            [ 0., 23.046, 88.939],
            [ 0., 10.637, 41.566]])
    """
    X_offset_param = params.pop("X_offset", None)
    X_scale_param = params.pop("X_scale", None)
    sample_weight = params.pop("sample_weight", None)
    tol = params.pop("tol", 1e-4)
    max_iter = params.pop("max_iter", 1000)
    random_state = params.pop("random_state", None)
    selection = params.pop("selection", "cyclic")
    do_screening = params.pop("do_screening", True)

    if len(params) > 0:
        raise ValueError("Unexpected parameters in params", params.keys())

    # We expect X and y to be already Fortran ordered when bypassing
    # checks
    if check_input:
        X = check_array(
            X,
            accept_sparse="csc",
            dtype=[np.float64, np.float32],
            order="F",
            copy=copy_X,
        )
        y = check_array(
            y,
            accept_sparse="csc",
            dtype=X.dtype.type,
            order="F",
            copy=False,
            ensure_2d=False,
        )
        if Xy is not None:
            # Xy should be a 1d contiguous array or a 2D C ordered array
            Xy = check_array(
                Xy, dtype=X.dtype.type, order="C", copy=False, ensure_2d=False
            )

    n_samples, n_features = X.shape

    multi_output = False
    if y.ndim != 1:
        multi_output = True
        n_targets = y.shape[1]

    if multi_output and positive:
        raise ValueError("positive=True is not allowed for multi-output (y.ndim != 1)")

    X_is_sparse = sparse.issparse(X)
    if X_is_sparse:
        if X_offset_param is not None:
            # As sparse matrices are not actually centered we need this to be passed to
            # the CD solver.
            X_sparse_scaling = X_offset_param / X_scale_param
            X_sparse_scaling = np.asarray(X_sparse_scaling, dtype=X.dtype)
        else:
            X_sparse_scaling = np.zeros(n_features, dtype=X.dtype)
    else:
        X_sparse_scaling = None

    # X should have been passed through _pre_fit already if function is called
    # from ElasticNet.fit
    if check_input or precompute is not False:
        X, y, _, _, _, precompute, Xy = _pre_fit(
            X,
            y,
            Xy,
            precompute,
            fit_intercept=False,
            copy=False,
            check_gram=check_input,
        )
    if alphas is None:
        # fit_intercept and sample_weight have already been dealt with in calling
        # methods like ElasticNet.fit.
        alphas = _alpha_grid(
            X,
            y,
            Xy=Xy,
            l1_ratio=l1_ratio,
            fit_intercept=False,
            positive=positive,
            eps=eps,
            n_alphas=n_alphas,
        )
    elif len(alphas) > 1:
        alphas = np.sort(alphas)[::-1]  # make sure alphas are properly ordered

    n_alphas = len(alphas)
    dual_gaps = np.empty(n_alphas)
    n_iters = []

    rng = check_random_state(random_state)
    if selection not in ["random", "cyclic"]:
        raise ValueError("selection should be either random or cyclic.")
    random = selection == "random"

    if not multi_output:
        coefs = np.empty((n_features, n_alphas), dtype=X.dtype)
    else:
        coefs = np.empty((n_targets, n_features, n_alphas), dtype=X.dtype)

    if coef_init is None:
        coef_ = np.zeros(coefs.shape[:-1], dtype=X.dtype, order="F")
    else:
        coef_ = np.asfortranarray(coef_init, dtype=X.dtype)

    if X_is_sparse:
        X_data = X.data
        X_indices = X.indices
        X_indptr = X.indptr
    else:
        X_data = None
        X_indices = None
        X_indptr = None

    for i, alpha in enumerate(alphas):
        # account for n_samples scaling in objectives between here and cd_fast
        l1_reg = alpha * l1_ratio * n_samples
        l2_reg = alpha * (1.0 - l1_ratio) * n_samples
        if not multi_output and X_is_sparse:
            model = cd_fast.sparse_enet_coordinate_descent(
                w=coef_,
                alpha=l1_reg,
                beta=l2_reg,
                X_data=X_data,
                X_indices=X_indices,
                X_indptr=X_indptr,
                y=y,
                sample_weight=sample_weight,
                X_mean=X_sparse_scaling,
                max_iter=max_iter,
                tol=tol,
                rng=rng,
                random=random,
                positive=positive,
                do_screening=do_screening,
            )
        elif multi_output:
            model = cd_fast.enet_coordinate_descent_multi_task(
                W=coef_,
                alpha=l1_reg,
                beta=l2_reg,
                X=None if X_is_sparse else X,
                X_is_sparse=X_is_sparse,
                X_data=X_data,
                X_indices=X_indices,
                X_indptr=X_indptr,
                Y=y,
                sample_weight=sample_weight,
                X_mean=X_sparse_scaling,
                max_iter=max_iter,
                tol=tol,
                rng=rng,
                random=random,
                do_screening=do_screening,
            )
        elif isinstance(precompute, np.ndarray):
            # We expect precompute to be already Fortran ordered when bypassing
            # checks
            if check_input:
                precompute = check_array(precompute, dtype=X.dtype.type, order="C")
            model = cd_fast.enet_coordinate_descent_gram(
                coef_,
                l1_reg,
                l2_reg,
                precompute,
                Xy,
                y,
                max_iter,
                tol,
                rng,
                random,
                positive,
                do_screening,
            )
        elif precompute is False:
            model = cd_fast.enet_coordinate_descent(
                coef_,
                l1_reg,
                l2_reg,
                X,
                y,
                max_iter,
                tol,
                rng,
                random,
                positive,
                do_screening,
            )
        else:
            raise ValueError(
                "Precompute should be one of True, False, 'auto' or array-like. Got %r"
                % precompute
            )
        coef_, dual_gap_, eps_, n_iter_ = model
        coefs[..., i] = coef_
        # we correct the scale of the returned dual gap, as the objective
        # in cd_fast is n_samples * the objective in this docstring.
        dual_gaps[i] = dual_gap_ / n_samples
        n_iters.append(n_iter_)

        if verbose:
            if verbose > 2:
                print(model)
            elif verbose > 1:
                print("Path: %03i out of %03i" % (i, n_alphas))
            else:
                sys.stderr.write(".")

    if return_n_iter:
        return alphas, coefs, dual_gaps, n_iters
    return alphas, coefs, dual_gaps