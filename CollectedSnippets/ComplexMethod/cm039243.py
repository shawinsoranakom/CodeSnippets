def from_estimator(
        cls,
        estimator,
        X,
        features,
        *,
        sample_weight=None,
        categorical_features=None,
        feature_names=None,
        target=None,
        response_method="auto",
        n_cols=3,
        grid_resolution=100,
        percentiles=(0.05, 0.95),
        custom_values=None,
        method="auto",
        n_jobs=None,
        verbose=0,
        line_kw=None,
        ice_lines_kw=None,
        pd_line_kw=None,
        contour_kw=None,
        ax=None,
        kind="average",
        centered=False,
        subsample=1000,
        random_state=None,
    ):
        """Partial dependence (PD) and individual conditional expectation (ICE) plots.

        Partial dependence plots, individual conditional expectation plots, or an
        overlay of both can be plotted by setting the `kind` parameter.
        This method generates one plot for each entry in `features`. The plots
        are arranged in a grid with `n_cols` columns. For one-way partial
        dependence plots, the deciles of the feature values are shown on the
        x-axis. For two-way plots, the deciles are shown on both axes and PDPs
        are contour plots.

        For general information regarding `scikit-learn` visualization tools, see
        the :ref:`Visualization Guide <visualizations>`.
        For guidance on interpreting these plots, refer to the
        :ref:`Inspection Guide <partial_dependence>`.

        For an example on how to use this class method, see
        :ref:`sphx_glr_auto_examples_inspection_plot_partial_dependence.py`.

        .. note::

            :func:`PartialDependenceDisplay.from_estimator` does not support using the
            same axes with multiple calls. To plot the partial dependence for
            multiple estimators, please pass the axes created by the first call to the
            second call::

               >>> from sklearn.inspection import PartialDependenceDisplay
               >>> from sklearn.datasets import make_friedman1
               >>> from sklearn.linear_model import LinearRegression
               >>> from sklearn.ensemble import RandomForestRegressor
               >>> X, y = make_friedman1()
               >>> est1 = LinearRegression().fit(X, y)
               >>> est2 = RandomForestRegressor().fit(X, y)
               >>> disp1 = PartialDependenceDisplay.from_estimator(est1, X,
               ...                                                 [1, 2])
               >>> disp2 = PartialDependenceDisplay.from_estimator(est2, X, [1, 2],
               ...                                                 ax=disp1.axes_)

        .. warning::

            For :class:`~sklearn.ensemble.GradientBoostingClassifier` and
            :class:`~sklearn.ensemble.GradientBoostingRegressor`, the
            `'recursion'` method (used by default) will not account for the `init`
            predictor of the boosting process. In practice, this will produce
            the same values as `'brute'` up to a constant offset in the target
            response, provided that `init` is a constant estimator (which is the
            default). However, if `init` is not a constant estimator, the
            partial dependence values are incorrect for `'recursion'` because the
            offset will be sample-dependent. It is preferable to use the `'brute'`
            method. Note that this only applies to
            :class:`~sklearn.ensemble.GradientBoostingClassifier` and
            :class:`~sklearn.ensemble.GradientBoostingRegressor`, not to
            :class:`~sklearn.ensemble.HistGradientBoostingClassifier` and
            :class:`~sklearn.ensemble.HistGradientBoostingRegressor`.

        .. versionadded:: 1.0

        Parameters
        ----------
        estimator : BaseEstimator
            A fitted estimator object implementing :term:`predict`,
            :term:`predict_proba`, or :term:`decision_function`.
            Multioutput-multiclass classifiers are not supported.

        X : {array-like, dataframe} of shape (n_samples, n_features)
            ``X`` is used to generate a grid of values for the target
            ``features`` (where the partial dependence will be evaluated), and
            also to generate values for the complement features when the
            `method` is `'brute'`.

        features : list of {int, str, pair of int, pair of str}
            The target features for which to create the PDPs.
            If `features[i]` is an integer or a string, a one-way PDP is created;
            if `features[i]` is a tuple, a two-way PDP is created (only supported
            with `kind='average'`). Each tuple must be of size 2.
            If any entry is a string, then it must be in ``feature_names``.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights are used to calculate weighted means when averaging the
            model output. If `None`, then samples are equally weighted. If
            `sample_weight` is not `None`, then `method` will be set to `'brute'`.
            Note that `sample_weight` is ignored for `kind='individual'`.

            .. versionadded:: 1.3

        categorical_features : array-like of shape (n_features,) or shape \
                (n_categorical_features,), dtype={bool, int, str}, default=None
            Indicates the categorical features.

            - `None`: no feature will be considered categorical;
            - boolean array-like: boolean mask of shape `(n_features,)`
              indicating which features are categorical. Thus, this array has
              the same shape has `X.shape[1]`;
            - integer or string array-like: integer indices or strings
              indicating categorical features.

            .. versionadded:: 1.2

        feature_names : array-like of shape (n_features,), dtype=str, default=None
            Name of each feature; `feature_names[i]` holds the name of the feature
            with index `i`.
            By default, the name of the feature corresponds to their numerical
            index for NumPy array and their column name for pandas dataframe.

        target : int, default=None
            - In a multiclass setting, specifies the class for which the PDPs
              should be computed. Note that for binary classification, the
              positive class (index 1) is always used.
            - In a multioutput setting, specifies the task for which the PDPs
              should be computed.

            Ignored in binary classification or classical regression settings.

        response_method : {'auto', 'predict_proba', 'decision_function'}, \
                default='auto'
            Specifies whether to use :term:`predict_proba` or
            :term:`decision_function` as the target response. For regressors
            this parameter is ignored and the response is always the output of
            :term:`predict`. By default, :term:`predict_proba` is tried first
            and we revert to :term:`decision_function` if it doesn't exist. If
            ``method`` is `'recursion'`, the response is always the output of
            :term:`decision_function`.

        n_cols : int, default=3
            The maximum number of columns in the grid plot. Only active when `ax`
            is a single axis or `None`.

        grid_resolution : int, default=100
            The number of equally spaced points on the axes of the plots, for each
            target feature.
            This parameter is overridden by `custom_values` if that parameter is set.

        percentiles : tuple of float, default=(0.05, 0.95)
            The lower and upper percentile used to create the extreme values
            for the PDP axes. Must be in [0, 1].
            This parameter is overridden by `custom_values` if that parameter is set.

        custom_values : dict
            A dictionary mapping the index of an element of `features` to an
            array of values where the partial dependence should be calculated
            for that feature. Setting a range of values for a feature overrides
            `grid_resolution` and `percentiles`.

            .. versionadded:: 1.7

        method : str, default='auto'
            The method used to calculate the averaged predictions:

            - `'recursion'` is only supported for some tree-based estimators
              (namely
              :class:`~sklearn.ensemble.GradientBoostingClassifier`,
              :class:`~sklearn.ensemble.GradientBoostingRegressor`,
              :class:`~sklearn.ensemble.HistGradientBoostingClassifier`,
              :class:`~sklearn.ensemble.HistGradientBoostingRegressor`,
              :class:`~sklearn.tree.DecisionTreeRegressor`,
              :class:`~sklearn.ensemble.RandomForestRegressor`
              but is more efficient in terms of speed.
              With this method, the target response of a
              classifier is always the decision function, not the predicted
              probabilities. Since the `'recursion'` method implicitly computes
              the average of the ICEs by design, it is not compatible with ICE and
              thus `kind` must be `'average'`.

            - `'brute'` is supported for any estimator, but is more
              computationally intensive.

            - `'auto'`: the `'recursion'` is used for estimators that support it,
              and `'brute'` is used otherwise. If `sample_weight` is not `None`,
              then `'brute'` is used regardless of the estimator.

            Please see :ref:`this note <pdp_method_differences>` for
            differences between the `'brute'` and `'recursion'` method.

        n_jobs : int, default=None
            The number of CPUs to use to compute the partial dependences.
            Computation is parallelized over features specified by the `features`
            parameter.

            ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
            ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
            for more details.

        verbose : int, default=0
            Verbose output during PD computations.

        line_kw : dict, default=None
            Dict with keywords passed to the ``matplotlib.pyplot.plot`` call.
            For one-way partial dependence plots. It can be used to define common
            properties for both `ice_lines_kw` and `pdp_line_kw`.

        ice_lines_kw : dict, default=None
            Dictionary with keywords passed to the `matplotlib.pyplot.plot` call.
            For ICE lines in the one-way partial dependence plots.
            The key value pairs defined in `ice_lines_kw` takes priority over
            `line_kw`.

        pd_line_kw : dict, default=None
            Dictionary with keywords passed to the `matplotlib.pyplot.plot` call.
            For partial dependence in one-way partial dependence plots.
            The key value pairs defined in `pd_line_kw` takes priority over
            `line_kw`.

        contour_kw : dict, default=None
            Dict with keywords passed to the ``matplotlib.pyplot.contourf`` call.
            For two-way partial dependence plots.

        ax : Matplotlib axes or array-like of Matplotlib axes, default=None
            - If a single axis is passed in, it is treated as a bounding axes
              and a grid of partial dependence plots will be drawn within
              these bounds. The `n_cols` parameter controls the number of
              columns in the grid.
            - If an array-like of axes are passed in, the partial dependence
              plots will be drawn directly into these axes.
            - If `None`, a figure and a bounding axes is created and treated
              as the single axes case.

        kind : {'average', 'individual', 'both'}, default='average'
            Whether to plot the partial dependence averaged across all the samples
            in the dataset or one line per sample or both.

            - ``kind='average'`` results in the traditional PD plot;
            - ``kind='individual'`` results in the ICE plot.

            Note that the fast `method='recursion'` option is only available for
            `kind='average'` and `sample_weights=None`. Computing individual
            dependencies and doing weighted averages requires using the slower
            `method='brute'`.

        centered : bool, default=False
            If `True`, the ICE and PD lines will start at the origin of the
            y-axis. By default, no centering is done.

            .. versionadded:: 1.1

        subsample : float, int or None, default=1000
            Sampling for ICE curves when `kind` is 'individual' or 'both'.
            If `float`, should be between 0.0 and 1.0 and represent the proportion
            of the dataset to be used to plot ICE curves. If `int`, represents the
            absolute number samples to use.

            Note that the full dataset is still used to calculate averaged partial
            dependence when `kind='both'`.

        random_state : int, RandomState instance or None, default=None
            Controls the randomness of the selected samples when subsamples is not
            `None` and `kind` is either `'both'` or `'individual'`.
            See :term:`Glossary <random_state>` for details.

        Returns
        -------
        display : :class:`~sklearn.inspection.PartialDependenceDisplay`

        See Also
        --------
        partial_dependence : Compute Partial Dependence values.

        Examples
        --------
        >>> import matplotlib.pyplot as plt
        >>> from sklearn.datasets import make_friedman1
        >>> from sklearn.ensemble import GradientBoostingRegressor
        >>> from sklearn.inspection import PartialDependenceDisplay
        >>> X, y = make_friedman1()
        >>> clf = GradientBoostingRegressor(n_estimators=10).fit(X, y)
        >>> PartialDependenceDisplay.from_estimator(clf, X, [0, (0, 1)])
        <...>
        >>> plt.show()
        """
        check_matplotlib_support(f"{cls.__name__}.from_estimator")
        import matplotlib.pyplot as plt

        # set target_idx for multi-class estimators
        if hasattr(estimator, "classes_") and np.size(estimator.classes_) > 2:
            if target is None:
                raise ValueError("target must be specified for multi-class")
            target_idx = np.searchsorted(estimator.classes_, target)
            if (
                not (0 <= target_idx < len(estimator.classes_))
                or estimator.classes_[target_idx] != target
            ):
                raise ValueError("target not in est.classes_, got {}".format(target))
        else:
            # regression and binary classification
            target_idx = 0

        # Use check_array only on lists and other non-array-likes / sparse. Do not
        # convert DataFrame into a NumPy array.
        if not (hasattr(X, "__array__") or sparse.issparse(X)):
            X = check_array(X, ensure_all_finite="allow-nan", dtype=object)
        n_features = X.shape[1]

        feature_names = _check_feature_names(X, feature_names)
        # expand kind to always be a list of str
        kind_ = [kind] * len(features) if isinstance(kind, str) else kind
        if len(kind_) != len(features):
            raise ValueError(
                "When `kind` is provided as a list of strings, it should contain "
                f"as many elements as `features`. `kind` contains {len(kind_)} "
                f"element(s) and `features` contains {len(features)} element(s)."
            )

        # convert features into a seq of int tuples
        tmp_features, ice_for_two_way_pd = [], []
        for kind_plot, fxs in zip(kind_, features):
            if isinstance(fxs, (numbers.Integral, str)):
                fxs = (fxs,)
            try:
                fxs = tuple(
                    _get_feature_index(fx, feature_names=feature_names) for fx in fxs
                )
            except TypeError as e:
                raise ValueError(
                    "Each entry in features must be either an int, "
                    "a string, or an iterable of size at most 2."
                ) from e
            if not 1 <= np.size(fxs) <= 2:
                raise ValueError(
                    "Each entry in features must be either an int, "
                    "a string, or an iterable of size at most 2."
                )
            # store the information if 2-way PD was requested with ICE to later
            # raise a ValueError with an exhaustive list of problematic
            # settings.
            ice_for_two_way_pd.append(kind_plot != "average" and np.size(fxs) > 1)

            tmp_features.append(fxs)

        if any(ice_for_two_way_pd):
            # raise an error and be specific regarding the parameter values
            # when 1- and 2-way PD were requested
            kind_ = [
                "average" if forcing_average else kind_plot
                for forcing_average, kind_plot in zip(ice_for_two_way_pd, kind_)
            ]
            raise ValueError(
                "ICE plot cannot be rendered for 2-way feature interactions. "
                "2-way feature interactions mandates PD plots using the "
                "'average' kind: "
                f"features={features!r} should be configured to use "
                f"kind={kind_!r} explicitly."
            )
        features = tmp_features

        if categorical_features is None:
            is_categorical = [
                (False,) if len(fxs) == 1 else (False, False) for fxs in features
            ]
        else:
            # we need to create a boolean indicator of which features are
            # categorical from the categorical_features list.
            categorical_features = np.asarray(categorical_features)
            if categorical_features.dtype.kind == "b":
                # categorical features provided as a list of boolean
                if categorical_features.size != n_features:
                    raise ValueError(
                        "When `categorical_features` is a boolean array-like, "
                        "the array should be of shape (n_features,). Got "
                        f"{categorical_features.size} elements while `X` contains "
                        f"{n_features} features."
                    )
                is_categorical = [
                    tuple(categorical_features[fx] for fx in fxs) for fxs in features
                ]
            elif categorical_features.dtype.kind in ("i", "O", "U"):
                # categorical features provided as a list of indices or feature names
                categorical_features_idx = [
                    _get_feature_index(cat, feature_names=feature_names)
                    for cat in categorical_features
                ]
                is_categorical = [
                    tuple([idx in categorical_features_idx for idx in fxs])
                    for fxs in features
                ]
            else:
                raise ValueError(
                    "Expected `categorical_features` to be an array-like of boolean,"
                    f" integer, or string. Got {categorical_features.dtype} instead."
                )

            for cats in is_categorical:
                if np.size(cats) == 2 and (cats[0] != cats[1]):
                    raise ValueError(
                        "Two-way partial dependence plots are not supported for pairs"
                        " of continuous and categorical features."
                    )

            # collect the indices of the categorical features targeted by the partial
            # dependence computation
            categorical_features_targeted = set(
                [
                    fx
                    for fxs, cats in zip(features, is_categorical)
                    for fx in fxs
                    if any(cats)
                ]
            )
            if categorical_features_targeted:
                min_n_cats = min(
                    [
                        len(_unique(_safe_indexing(X, idx, axis=1)))
                        for idx in categorical_features_targeted
                    ]
                )
                if grid_resolution < min_n_cats:
                    raise ValueError(
                        "The resolution of the computed grid is less than the "
                        "minimum number of categories in the targeted categorical "
                        "features. Expect the `grid_resolution` to be greater than "
                        f"{min_n_cats}. Got {grid_resolution} instead."
                    )

            for is_cat, kind_plot in zip(is_categorical, kind_):
                if any(is_cat) and kind_plot != "average":
                    raise ValueError(
                        "It is not possible to display individual effects for"
                        " categorical features."
                    )

        # Early exit if the axes does not have the correct number of axes
        if ax is not None and not isinstance(ax, plt.Axes):
            axes = np.asarray(ax, dtype=object)
            if axes.size != len(features):
                raise ValueError(
                    "Expected ax to have {} axes, got {}".format(
                        len(features), axes.size
                    )
                )

        for i in chain.from_iterable(features):
            if i >= len(feature_names):
                raise ValueError(
                    "All entries of features must be less than "
                    "len(feature_names) = {0}, got {1}.".format(len(feature_names), i)
                )

        if isinstance(subsample, numbers.Integral):
            if subsample <= 0:
                raise ValueError(
                    f"When an integer, subsample={subsample} should be positive."
                )
        elif isinstance(subsample, numbers.Real):
            if subsample <= 0 or subsample >= 1:
                raise ValueError(
                    f"When a floating-point, subsample={subsample} should be in "
                    "the (0, 1) range."
                )

        # compute predictions and/or averaged predictions
        pd_results = Parallel(n_jobs=n_jobs, verbose=verbose)(
            delayed(partial_dependence)(
                estimator,
                X,
                fxs,
                sample_weight=sample_weight,
                feature_names=feature_names,
                categorical_features=categorical_features,
                response_method=response_method,
                method=method,
                grid_resolution=grid_resolution,
                percentiles=percentiles,
                kind=kind_plot,
                custom_values=custom_values,
            )
            for kind_plot, fxs in zip(kind_, features)
        )

        # For multioutput regression, we can only check the validity of target
        # now that we have the predictions.
        # Also note: as multiclass-multioutput classifiers are not supported,
        # multiclass and multioutput scenario are mutually exclusive. So there is
        # no risk of overwriting target_idx here.
        pd_result = pd_results[0]  # checking the first result is enough
        n_tasks = (
            pd_result.average.shape[0]
            if kind_[0] == "average"
            else pd_result.individual.shape[0]
        )
        if is_regressor(estimator) and n_tasks > 1:
            if target is None:
                raise ValueError("target must be specified for multi-output regressors")
            if not 0 <= target <= n_tasks:
                raise ValueError(
                    "target must be in [0, n_tasks], got {}.".format(target)
                )
            target_idx = target

        deciles = {}
        for fxs, cats in zip(features, is_categorical):
            for fx, cat in zip(fxs, cats):
                if not cat and fx not in deciles:
                    X_col = _safe_indexing(X, fx, axis=1)
                    deciles[fx] = mquantiles(X_col, prob=np.arange(0.1, 1.0, 0.1))

        display = cls(
            pd_results=pd_results,
            features=features,
            feature_names=feature_names,
            target_idx=target_idx,
            deciles=deciles,
            kind=kind,
            subsample=subsample,
            random_state=random_state,
            is_categorical=is_categorical,
        )
        return display.plot(
            ax=ax,
            n_cols=n_cols,
            line_kw=line_kw,
            ice_lines_kw=ice_lines_kw,
            pd_line_kw=pd_line_kw,
            contour_kw=contour_kw,
            centered=centered,
        )