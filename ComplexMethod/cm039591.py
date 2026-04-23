def _log_reg_scoring_path(
    X,
    y,
    train,
    test,
    *,
    classes,
    Cs,
    scoring,
    fit_intercept,
    max_iter,
    tol,
    class_weight,
    verbose,
    solver,
    penalty,
    dual,
    intercept_scaling,
    random_state,
    max_squared_sum,
    sample_weight,
    l1_ratio,
    score_params,
):
    """Computes scores across logistic_regression_path

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Training data.

    y : array-like of shape (n_samples,) or (n_samples, n_targets)
        Target labels.

    train : list of indices
        The indices of the train set.

    test : list of indices
        The indices of the test set.

    classes : ndarray
        A list of class labels known to the classifier.

    Cs : int or list of floats
        Each of the values in Cs describes the inverse of
        regularization strength. If Cs is as an int, then a grid of Cs
        values are chosen in a logarithmic scale between 1e-4 and 1e4.

    scoring : str, callable or None
        The scoring method to use for cross-validation. Options:

        - str: see :ref:`scoring_string_names` for options.
        - callable: a scorer callable object (e.g., function) with signature
          ``scorer(estimator, X, y)``. See :ref:`scoring_callable` for details.
        - `None`: :ref:`accuracy <accuracy_score>` is used.

    fit_intercept : bool
        If False, then the bias term is set to zero. Else the last
        term of each coef_ gives us the intercept.

    max_iter : int
        Maximum number of iterations for the solver.

    tol : float
        Tolerance for stopping criteria.

    class_weight : dict or 'balanced'
        Weights associated with classes in the form ``{class_label: weight}``.
        If not given, all classes are supposed to have weight one.

        The "balanced" mode uses the values of y to automatically adjust
        weights inversely proportional to class frequencies in the input data
        as ``n_samples / (n_classes * np.bincount(y))``

        Note that these weights will be multiplied with sample_weight (passed
        through the fit method) if sample_weight is specified.

    verbose : int
        For the liblinear and lbfgs solvers set verbose to any positive
        number for verbosity.

    solver : {'lbfgs', 'liblinear', 'newton-cg', 'newton-cholesky', 'sag', 'saga'}
        Decides which solver to use.

    penalty : {'l1', 'l2', 'elasticnet'}
        Used to specify the norm used in the penalization. The 'newton-cg',
        'sag' and 'lbfgs' solvers support only l2 penalties. 'elasticnet' is
        only supported by the 'saga' solver.

    dual : bool
        Dual or primal formulation. Dual formulation is only implemented for
        l2 penalty with liblinear solver. Prefer dual=False when
        n_samples > n_features.

    intercept_scaling : float
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

    random_state : int, RandomState instance
        Used when ``solver`` == 'sag', 'saga' or 'liblinear' to shuffle the
        data. See :term:`Glossary <random_state>` for details.

    max_squared_sum : float
        Maximum squared sum of X over samples. Used only in SAG solver.
        If None, it will be computed, going through all the samples.
        The value should be precomputed to speed up cross validation.

    sample_weight : array-like of shape (n_samples,)
        Array of weights that are assigned to individual samples.
        If not provided, then each sample is given unit weight.

    l1_ratio : float
        The Elastic-Net mixing parameter, with ``0 <= l1_ratio <= 1``. Only
        used if ``penalty='elasticnet'``. Setting ``l1_ratio=0`` is equivalent
        to using ``penalty='l2'``, while setting ``l1_ratio=1`` is equivalent
        to using ``penalty='l1'``. For ``0 < l1_ratio <1``, the penalty is a
        combination of L1 and L2.

    score_params : dict
        Parameters to pass to the `score` method of the underlying scorer.

    Returns
    -------
    coefs : ndarray of shape (n_cs, n_classes, n_features + int(fit_intercept)) or \
            (n_cs, n_features + int(fit_intercept))
        List of coefficients for the Logistic Regression model. If fit_intercept is set
        to True, then the last dimension will be n_features + 1, where the last item
        represents the intercept.
        For binary problems the second dimension in n_classes is dropped, i.e. the shape
        will be `(n_cs, n_features + int(fit_intercept))`.

    Cs : ndarray of shape (n_cs,)
        Grid of Cs used for cross-validation.

    scores : ndarray of shape (n_cs,)
        Scores obtained for each Cs.

    n_iter : ndarray of shape (n_cs,)
        Actual number of iteration for each C in Cs.
    """
    X_train = X[train]
    X_test = X[test]
    y_train = y[train]
    y_test = y[test]

    sw_train, sw_test = None, None
    if sample_weight is not None:
        sample_weight = _check_sample_weight(sample_weight, X)
        sw_train = sample_weight[train]
        sw_test = sample_weight[test]

    # Note: We pass classes for the whole dataset to avoid inconsistencies,
    # i.e. different number of classes in different folds. This way, if a class
    # is not present in a fold, _logistic_regression_path will still return
    # coefficients associated to this class.
    coefs, Cs, n_iter = _logistic_regression_path(
        X_train,
        y_train,
        classes=classes,
        Cs=Cs,
        l1_ratio=l1_ratio,
        fit_intercept=fit_intercept,
        solver=solver,
        max_iter=max_iter,
        class_weight=class_weight,
        tol=tol,
        verbose=verbose,
        dual=dual,
        penalty=penalty,
        intercept_scaling=intercept_scaling,
        random_state=random_state,
        check_input=False,
        max_squared_sum=max_squared_sum,
        sample_weight=sw_train,
    )

    log_reg = LogisticRegression(solver=solver)

    # The score method of Logistic Regression has a classes_ attribute.
    log_reg.classes_ = classes

    scores = list()

    # Prepare the call to get the score per fold: calc_score
    scoring = get_scorer(scoring)
    if scoring is None:

        def calc_score(log_reg):
            return log_reg.score(X_test, y_test, sample_weight=sw_test)

    else:
        is_binary = len(classes) <= 2
        score_params = score_params or {}
        score_params = _check_method_params(X=X, params=score_params, indices=test)
        # We need to pass the classes as "labels" argument to scorers that support
        # it, e.g. scoring = "neg_brier_score", because y_test may not contain all
        # class labels.
        # There are at least 2 possibilities:
        # 1. Metadata routing is enabled: A try except clause is possible with
        #   adding labels to score_params. We could then pass the already instantiated
        #   log_reg instance to scoring.
        # 2. We reconstruct the scorer and pass labels as kwargs explicitly.
        # We implement the 2nd option even if it seems a bit hacky because it works
        # with and without metadata routing.
        if hasattr(scoring, "_score_func"):
            sig = inspect.signature(scoring._score_func).parameters
        else:
            sig = []

        if "labels" in sig:
            pos_label_kwarg = {}
            if is_binary and "pos_label" in sig:
                # see _logistic_regression_path
                pos_label_kwarg["pos_label"] = classes[-1]
            scoring = make_scorer(
                scoring._score_func,
                greater_is_better=True if scoring._sign == 1 else False,
                response_method=scoring._response_method,
                labels=classes,
                **pos_label_kwarg,
                **getattr(scoring, "_kwargs", {}),
            )

        def calc_score(log_reg):
            return scoring(log_reg, X_test, y_test, **score_params)

    for w, C in zip(coefs, Cs):
        log_reg.C = C
        if fit_intercept:
            log_reg.coef_ = w[..., :-1]
            log_reg.intercept_ = w[..., -1]
        else:
            log_reg.coef_ = w
            log_reg.intercept_ = 0.0

        scores.append(calc_score(log_reg))

    return coefs, Cs, np.array(scores), n_iter