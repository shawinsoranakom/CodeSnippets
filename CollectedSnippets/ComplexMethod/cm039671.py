def learning_curve(
    estimator,
    X,
    y,
    *,
    groups=None,
    train_sizes=np.linspace(0.1, 1.0, 5),
    cv=None,
    scoring=None,
    exploit_incremental_learning=False,
    n_jobs=None,
    pre_dispatch="all",
    verbose=0,
    shuffle=False,
    random_state=None,
    error_score=np.nan,
    return_times=False,
    params=None,
):
    """Learning curve.

    Determines cross-validated training and test scores for different training
    set sizes.

    A cross-validation generator splits the whole dataset k times in training
    and test data. Subsets of the training set with varying sizes will be used
    to train the estimator and a score for each training subset size and the
    test set will be computed. Afterwards, the scores will be averaged over
    all k runs for each training subset size.

    Read more in the :ref:`User Guide <learning_curve>`.

    Parameters
    ----------
    estimator : object type that implements the "fit" method
        An object of that type which is cloned for each validation. It must
        also implement "predict" unless `scoring` is a callable that doesn't
        rely on "predict" to compute a score.

    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Training vector, where `n_samples` is the number of samples and
        `n_features` is the number of features.

    y : array-like of shape (n_samples,) or (n_samples, n_outputs) or None
        Target relative to X for classification or regression;
        None for unsupervised learning.

    groups : array-like of shape (n_samples,), default=None
        Group labels for the samples used while splitting the dataset into
        train/test set. Only used in conjunction with a "Group" :term:`cv`
        instance (e.g., :class:`GroupKFold`).

        .. versionchanged:: 1.6
            ``groups`` can only be passed if metadata routing is not enabled
            via ``sklearn.set_config(enable_metadata_routing=True)``. When routing
            is enabled, pass ``groups`` alongside other metadata via the ``params``
            argument instead. E.g.:
            ``learning_curve(..., params={'groups': groups})``.

    train_sizes : array-like of shape (n_ticks,), \
            default=np.linspace(0.1, 1.0, 5)
        Relative or absolute numbers of training examples that will be used to
        generate the learning curve. If the dtype is float, it is regarded as a
        fraction of the maximum size of the training set (that is determined
        by the selected validation method), i.e. it has to be within (0, 1].
        Otherwise it is interpreted as absolute sizes of the training sets.
        Note that for classification the number of samples usually has to
        be big enough to contain at least one sample from each class.

    cv : int, cross-validation generator or an iterable, default=None
        Determines the cross-validation splitting strategy.
        Possible inputs for cv are:

        - None, to use the default 5-fold cross validation,
        - int, to specify the number of folds in a `(Stratified)KFold`,
        - :term:`CV splitter`,
        - an iterable yielding (train, test) splits as arrays of indices.

        For int/None inputs, if the estimator is a classifier and ``y`` is
        either binary or multiclass, :class:`StratifiedKFold` is used. In all
        other cases, :class:`KFold` is used. These splitters are instantiated
        with `shuffle=False` so the splits will be the same across calls.

        Refer :ref:`User Guide <cross_validation>` for the various
        cross-validation strategies that can be used here.

        .. versionchanged:: 0.22
            ``cv`` default value if None changed from 3-fold to 5-fold.

    scoring : str or callable, default=None
        Scoring method to use to evaluate the training and test sets.

        - str: see :ref:`scoring_string_names` for options.
        - callable: a scorer callable object (e.g., function) with signature
          ``scorer(estimator, X, y)``. See :ref:`scoring_callable` for details.
        - `None`: the `estimator`'s
          :ref:`default evaluation criterion <scoring_api_overview>` is used.

    exploit_incremental_learning : bool, default=False
        If the estimator supports incremental learning, this will be
        used to speed up fitting for different training set sizes.

    n_jobs : int, default=None
        Number of jobs to run in parallel. Training the estimator and computing
        the score are parallelized over the different training and test sets.
        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
        for more details.

    pre_dispatch : int or str, default='all'
        Number of predispatched jobs for parallel execution (default is
        all). The option can reduce the allocated memory. The str can
        be an expression like '2*n_jobs'.

    verbose : int, default=0
        Controls the verbosity: the higher, the more messages.

    shuffle : bool, default=False
        Whether to shuffle training data before taking prefixes of it
        based on``train_sizes``.

    random_state : int, RandomState instance or None, default=None
        Used when ``shuffle`` is True. Pass an int for reproducible
        output across multiple function calls.
        See :term:`Glossary <random_state>`.

    error_score : 'raise' or numeric, default=np.nan
        Value to assign to the score if an error occurs in estimator fitting.
        If set to 'raise', the error is raised.
        If a numeric value is given, FitFailedWarning is raised.

        .. versionadded:: 0.20

    return_times : bool, default=False
        Whether to return the fit and score times.

    params : dict, default=None
        Parameters to pass to the `fit` method of the estimator and to the scorer.

        - If `enable_metadata_routing=False` (default): Parameters directly passed to
          the `fit` method of the estimator.

        - If `enable_metadata_routing=True`: Parameters safely routed to the `fit`
          method of the estimator. See :ref:`Metadata Routing User Guide
          <metadata_routing>` for more details.

        .. versionadded:: 1.6

    Returns
    -------
    train_sizes_abs : array of shape (n_unique_ticks,)
        Numbers of training examples that has been used to generate the
        learning curve. Note that the number of ticks might be less
        than n_ticks because duplicate entries will be removed.

    train_scores : array of shape (n_ticks, n_cv_folds)
        Scores on training sets.

    test_scores : array of shape (n_ticks, n_cv_folds)
        Scores on test set.

    fit_times : array of shape (n_ticks, n_cv_folds)
        Times spent for fitting in seconds. Only present if ``return_times``
        is True.

    score_times : array of shape (n_ticks, n_cv_folds)
        Times spent for scoring in seconds. Only present if ``return_times``
        is True.

    See Also
    --------
    LearningCurveDisplay.from_estimator : Plot a learning curve using an
        estimator and data.

    Examples
    --------
    >>> from sklearn.datasets import make_classification
    >>> from sklearn.tree import DecisionTreeClassifier
    >>> from sklearn.model_selection import learning_curve
    >>> X, y = make_classification(n_samples=100, n_features=10, random_state=42)
    >>> tree = DecisionTreeClassifier(max_depth=4, random_state=42)
    >>> train_size_abs, train_scores, test_scores = learning_curve(
    ...     tree, X, y, train_sizes=[0.3, 0.6, 0.9]
    ... )
    >>> for train_size, cv_train_scores, cv_test_scores in zip(
    ...     train_size_abs, train_scores, test_scores
    ... ):
    ...     print(f"{train_size} samples were used to train the model")
    ...     print(f"The average train accuracy is {cv_train_scores.mean():.2f}")
    ...     print(f"The average test accuracy is {cv_test_scores.mean():.2f}")
    24 samples were used to train the model
    The average train accuracy is 1.00
    The average test accuracy is 0.85
    48 samples were used to train the model
    The average train accuracy is 1.00
    The average test accuracy is 0.90
    72 samples were used to train the model
    The average train accuracy is 1.00
    The average test accuracy is 0.93
    """
    if exploit_incremental_learning and not hasattr(estimator, "partial_fit"):
        raise ValueError(
            "An estimator must support the partial_fit interface "
            "to exploit incremental learning"
        )
    _check_groups_routing_disabled(groups)
    params = {} if params is None else params

    X, y, groups = indexable(X, y, groups)

    cv = check_cv(cv, y, classifier=is_classifier(estimator))

    scorer = check_scoring(estimator, scoring=scoring)

    if _routing_enabled():
        router = (
            MetadataRouter(owner="learning_curve")
            .add(
                estimator=estimator,
                # TODO(SLEP6): also pass metadata to the predict method for
                # scoring?
                method_mapping=MethodMapping()
                .add(caller="fit", callee="fit")
                .add(caller="fit", callee="partial_fit"),
            )
            .add(
                splitter=cv,
                method_mapping=MethodMapping().add(caller="fit", callee="split"),
            )
            .add(
                scorer=scorer,
                method_mapping=MethodMapping().add(caller="fit", callee="score"),
            )
        )

        try:
            routed_params = process_routing(router, "fit", **params)
        except UnsetMetadataPassedError as e:
            # The default exception would mention `fit` since in the above
            # `process_routing` code, we pass `fit` as the caller. However,
            # the user is not calling `fit` directly, so we change the message
            # to make it more suitable for this case.
            raise UnsetMetadataPassedError(
                message=str(e).replace("learning_curve.fit", "learning_curve"),
                unrequested_params=e.unrequested_params,
                routed_params=e.routed_params,
            )

    else:
        routed_params = Bunch()
        routed_params.estimator = Bunch(fit=params, partial_fit=params)
        routed_params.splitter = Bunch(split={"groups": groups})
        routed_params.scorer = Bunch(score={})

    # Store cv as list as we will be iterating over the list multiple times
    cv_iter = list(cv.split(X, y, **routed_params.splitter.split))

    n_max_training_samples = len(cv_iter[0][0])
    # Because the lengths of folds can be significantly different, it is
    # not guaranteed that we use all of the available training data when we
    # use the first 'n_max_training_samples' samples.
    train_sizes_abs = _translate_train_sizes(train_sizes, n_max_training_samples)
    n_unique_ticks = train_sizes_abs.shape[0]
    if verbose > 0:
        print("[learning_curve] Training set sizes: " + str(train_sizes_abs))

    parallel = Parallel(n_jobs=n_jobs, pre_dispatch=pre_dispatch, verbose=verbose)

    if shuffle:
        rng = check_random_state(random_state)
        cv_iter = ((rng.permutation(train), test) for train, test in cv_iter)

    if exploit_incremental_learning:
        classes = np.unique(y) if is_classifier(estimator) else None
        out = parallel(
            delayed(_incremental_fit_estimator)(
                clone(estimator),
                X,
                y,
                classes,
                train,
                test,
                train_sizes_abs,
                scorer,
                return_times,
                error_score=error_score,
                fit_params=routed_params.estimator.partial_fit,
                score_params=routed_params.scorer.score,
            )
            for train, test in cv_iter
        )
        out = np.asarray(out).transpose((2, 1, 0))
    else:
        train_test_proportions = []
        for train, test in cv_iter:
            for n_train_samples in train_sizes_abs:
                train_test_proportions.append((train[:n_train_samples], test))

        results = parallel(
            delayed(_fit_and_score)(
                clone(estimator),
                X,
                y,
                scorer=scorer,
                train=train,
                test=test,
                verbose=verbose,
                parameters=None,
                fit_params=routed_params.estimator.fit,
                score_params=routed_params.scorer.score,
                return_train_score=True,
                error_score=error_score,
                return_times=return_times,
            )
            for train, test in train_test_proportions
        )
        _warn_or_raise_about_fit_failures(results, error_score)
        results = _aggregate_score_dicts(results)
        train_scores = results["train_scores"].reshape(-1, n_unique_ticks).T
        test_scores = results["test_scores"].reshape(-1, n_unique_ticks).T
        out = [train_scores, test_scores]

        if return_times:
            fit_times = results["fit_time"].reshape(-1, n_unique_ticks).T
            score_times = results["score_time"].reshape(-1, n_unique_ticks).T
            out.extend([fit_times, score_times])

    ret = train_sizes_abs, out[0], out[1]

    if return_times:
        ret = ret + (out[2], out[3])

    return ret