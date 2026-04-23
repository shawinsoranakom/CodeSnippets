def fit(self, X, y, sample_weight=None, **fit_params):
        """Fit estimator using RANSAC algorithm.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target values.

        sample_weight : array-like of shape (n_samples,), default=None
            Individual weights for each sample
            raises error if sample_weight is passed and estimator
            fit method does not support it.

            .. versionadded:: 0.18

        **fit_params : dict
            Parameters routed to the `fit` method of the sub-estimator via the
            metadata routing API.

            .. versionadded:: 1.5

                Only available if
                `sklearn.set_config(enable_metadata_routing=True)` is set. See
                :ref:`Metadata Routing User Guide <metadata_routing>` for more
                details.

        Returns
        -------
        self : object
            Fitted `RANSACRegressor` estimator.

        Raises
        ------
        ValueError
            If no valid consensus set could be found. This occurs if
            `is_data_valid` and `is_model_valid` return False for all
            `max_trials` randomly chosen sub-samples.
        """
        # Need to validate separately here. We can't pass multi_output=True
        # because that would allow y to be csr. Delay expensive finiteness
        # check to the estimator's own input validation.
        _raise_for_params(fit_params, self, "fit")
        check_X_params = dict(accept_sparse="csr", ensure_all_finite=False)
        check_y_params = dict(ensure_2d=False)
        X, y = validate_data(
            self, X, y, validate_separately=(check_X_params, check_y_params)
        )
        check_consistent_length(X, y)

        if self.estimator is not None:
            estimator = clone(self.estimator)
        else:
            estimator = LinearRegression()

        if self.min_samples is None:
            if not isinstance(estimator, LinearRegression):
                raise ValueError(
                    "`min_samples` needs to be explicitly set when estimator "
                    "is not a LinearRegression."
                )
            min_samples = X.shape[1] + 1
        elif 0 < self.min_samples < 1:
            min_samples = np.ceil(self.min_samples * X.shape[0])
        elif self.min_samples >= 1:
            min_samples = self.min_samples
        if min_samples > X.shape[0]:
            raise ValueError(
                "`min_samples` may not be larger than number "
                "of samples: n_samples = %d." % (X.shape[0])
            )

        if self.residual_threshold is None:
            # MAD (median absolute deviation)
            residual_threshold = np.median(np.abs(y - np.median(y)))
        else:
            residual_threshold = self.residual_threshold

        if self.loss == "absolute_error":
            if y.ndim == 1:
                loss_function = lambda y_true, y_pred: np.abs(y_true - y_pred)
            else:
                loss_function = lambda y_true, y_pred: np.sum(
                    np.abs(y_true - y_pred), axis=1
                )
        elif self.loss == "squared_error":
            if y.ndim == 1:
                loss_function = lambda y_true, y_pred: (y_true - y_pred) ** 2
            else:
                loss_function = lambda y_true, y_pred: np.sum(
                    (y_true - y_pred) ** 2, axis=1
                )

        elif callable(self.loss):
            loss_function = self.loss

        random_state = check_random_state(self.random_state)

        try:  # Not all estimator accept a random_state
            estimator.set_params(random_state=random_state)
        except ValueError:
            pass

        estimator_fit_has_sample_weight = has_fit_parameter(estimator, "sample_weight")
        estimator_name = type(estimator).__name__
        if sample_weight is not None and not estimator_fit_has_sample_weight:
            raise ValueError(
                "%s does not support sample_weight. Sample"
                " weights are only used for the calibration"
                " itself." % estimator_name
            )

        if sample_weight is not None:
            fit_params["sample_weight"] = sample_weight

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **fit_params)
        else:
            routed_params = Bunch()
            routed_params.estimator = Bunch(fit={}, predict={}, score={})
            if sample_weight is not None:
                sample_weight = _check_sample_weight(sample_weight, X)
                routed_params.estimator.fit = {"sample_weight": sample_weight}

        n_inliers_best = 1
        score_best = -np.inf
        inlier_mask_best = None
        X_inlier_best = None
        y_inlier_best = None
        inlier_best_idxs_subset = None
        self.n_skips_no_inliers_ = 0
        self.n_skips_invalid_data_ = 0
        self.n_skips_invalid_model_ = 0

        # number of data samples
        n_samples = X.shape[0]
        sample_idxs = np.arange(n_samples)

        self.n_trials_ = 0
        max_trials = self.max_trials
        while self.n_trials_ < max_trials:
            self.n_trials_ += 1

            if (
                self.n_skips_no_inliers_
                + self.n_skips_invalid_data_
                + self.n_skips_invalid_model_
            ) > self.max_skips:
                break

            # choose random sample set
            subset_idxs = sample_without_replacement(
                n_samples, min_samples, random_state=random_state
            )
            X_subset = X[subset_idxs]
            y_subset = y[subset_idxs]

            # check if random sample set is valid
            if self.is_data_valid is not None and not self.is_data_valid(
                X_subset, y_subset
            ):
                self.n_skips_invalid_data_ += 1
                continue

            # cut `fit_params` down to `subset_idxs`
            fit_params_subset = _check_method_params(
                X, params=routed_params.estimator.fit, indices=subset_idxs
            )

            # fit model for current random sample set
            estimator.fit(X_subset, y_subset, **fit_params_subset)

            # check if estimated model is valid
            if self.is_model_valid is not None and not self.is_model_valid(
                estimator, X_subset, y_subset
            ):
                self.n_skips_invalid_model_ += 1
                continue

            # residuals of all data for current random sample model
            y_pred = estimator.predict(X)
            residuals_subset = loss_function(y, y_pred)

            # classify data into inliers and outliers
            inlier_mask_subset = residuals_subset <= residual_threshold
            n_inliers_subset = np.sum(inlier_mask_subset)

            # less inliers -> skip current random sample
            if n_inliers_subset < n_inliers_best:
                self.n_skips_no_inliers_ += 1
                continue

            # extract inlier data set
            inlier_idxs_subset = sample_idxs[inlier_mask_subset]
            X_inlier_subset = X[inlier_idxs_subset]
            y_inlier_subset = y[inlier_idxs_subset]

            # cut `fit_params` down to `inlier_idxs_subset`
            score_params_inlier_subset = _check_method_params(
                X, params=routed_params.estimator.score, indices=inlier_idxs_subset
            )

            # score of inlier data set
            score_subset = estimator.score(
                X_inlier_subset,
                y_inlier_subset,
                **score_params_inlier_subset,
            )

            # same number of inliers but worse score -> skip current random
            # sample
            if n_inliers_subset == n_inliers_best and score_subset < score_best:
                continue

            # save current random sample as best sample
            n_inliers_best = n_inliers_subset
            score_best = score_subset
            inlier_mask_best = inlier_mask_subset
            X_inlier_best = X_inlier_subset
            y_inlier_best = y_inlier_subset
            inlier_best_idxs_subset = inlier_idxs_subset

            max_trials = min(
                max_trials,
                _dynamic_max_trials(
                    n_inliers_best, n_samples, min_samples, self.stop_probability
                ),
            )

            # break if sufficient number of inliers or score is reached
            if n_inliers_best >= self.stop_n_inliers or score_best >= self.stop_score:
                break

        # if none of the iterations met the required criteria
        if inlier_mask_best is None:
            if (
                self.n_skips_no_inliers_
                + self.n_skips_invalid_data_
                + self.n_skips_invalid_model_
            ) > self.max_skips:
                raise ValueError(
                    "RANSAC skipped more iterations than `max_skips` without"
                    " finding a valid consensus set. Iterations were skipped"
                    " because each randomly chosen sub-sample failed the"
                    " passing criteria. See estimator attributes for"
                    " diagnostics (n_skips*)."
                )
            else:
                raise ValueError(
                    "RANSAC could not find a valid consensus set. All"
                    " `max_trials` iterations were skipped because each"
                    " randomly chosen sub-sample failed the passing criteria."
                    " See estimator attributes for diagnostics (n_skips*)."
                )
        else:
            if (
                self.n_skips_no_inliers_
                + self.n_skips_invalid_data_
                + self.n_skips_invalid_model_
            ) > self.max_skips:
                warnings.warn(
                    (
                        "RANSAC found a valid consensus set but exited"
                        " early due to skipping more iterations than"
                        " `max_skips`. See estimator attributes for"
                        " diagnostics (n_skips*)."
                    ),
                    ConvergenceWarning,
                )

        # estimate final model using all inliers
        fit_params_best_idxs_subset = _check_method_params(
            X, params=routed_params.estimator.fit, indices=inlier_best_idxs_subset
        )

        estimator.fit(X_inlier_best, y_inlier_best, **fit_params_best_idxs_subset)

        self.estimator_ = estimator
        self.inlier_mask_ = inlier_mask_best
        return self