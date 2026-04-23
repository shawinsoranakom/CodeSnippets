def fit(self, X, y, sample_weight=None, score_params=None):
        """Fit Ridge regression model with gcv.

        Parameters
        ----------
        X : {ndarray, sparse matrix} of shape (n_samples, n_features)
            Training data. Will be cast to float64 if necessary.

        y : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Target values. Will be cast to float64 if necessary.

        sample_weight : float or ndarray of shape (n_samples,), default=None
            Individual weights for each sample. If given a float, every sample
            will have the same weight. Note that the scale of `sample_weight`
            has an impact on the loss; i.e. multiplying all weights by `k`
            is equivalent to setting `alpha / k`.

        score_params : dict, default=None
            Parameters to be passed to the underlying scorer.

            .. versionadded:: 1.5
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
        """
        xp, is_array_api, device_ = get_namespace_and_device(X)
        y, sample_weight = move_to(y, sample_weight, xp=xp, device=device_)
        if (is_array_api and xp.isdtype(X.dtype, "real floating")) or getattr(
            getattr(X, "dtype", None), "kind", None
        ) == "f":
            original_floating_dtype = X.dtype
        else:
            # for X that does not have a simple dtype (e.g. pandas dataframe)
            # the attributes will be stored in the dtype chosen by
            # `validate_data``, i.e. np.float64
            original_floating_dtype = None
        # Using float32 can be numerically unstable for this estimator. So if
        # the array API namespace and device allow, convert the input values
        # to float64 whenever possible before converting the results back to
        # float32.
        dtype = _max_precision_float_dtype(xp, device=device_)
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csr", "csc", "coo"],
            dtype=dtype,
            multi_output=True,
            y_numeric=True,
        )

        # alpha_per_target cannot be used in classifier mode. All subclasses
        # of _RidgeGCV that are classifiers keep alpha_per_target at its
        # default value: False, so the condition below should never happen.
        assert not (self.is_clf and self.alpha_per_target)

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        self.alphas = np.asarray(self.alphas)

        unscaled_y = y
        X, y, X_offset, y_offset, X_scale, sqrt_sw = _preprocess_data(
            X,
            y,
            fit_intercept=self.fit_intercept,
            copy=self.copy_X,
            sample_weight=sample_weight,
            rescale_with_sw=True,
        )

        gcv_mode = _check_gcv_mode(X, self.gcv_mode)

        n_samples, n_features = X.shape
        if gcv_mode == "gram":
            decompose = self._eigen_decompose_gram
            solve = self._solve_eigen_gram
        elif gcv_mode == "cov":
            decompose = self._eigen_decompose_covariance
            solve = self._solve_eigen_covariance
        elif gcv_mode == "svd":
            decompose = self._svd_decompose_design_matrix
            solve = self._solve_svd_design_matrix
        else:
            raise ValueError(f"Unknown {gcv_mode=}")

        if sqrt_sw is None:
            sqrt_sw = xp.ones(n_samples, dtype=X.dtype, device=device_)

        decomposition = decompose(X, X_offset, y, sqrt_sw)

        n_y = 1 if y.ndim == 1 else y.shape[1]
        if (
            isinstance(self.alphas, numbers.Number)
            or getattr(self.alphas, "ndim", None) == 0
        ):
            alphas = [float(self.alphas)]
        else:
            alphas = list(map(float, self.alphas))
        n_alphas = len(alphas)

        if self.store_cv_results:
            self.cv_results_ = xp.empty(
                (n_samples * n_y, n_alphas), dtype=X.dtype, device=device_
            )

        best_coef, best_score, best_alpha = None, None, None

        for i, alpha in enumerate(alphas):
            looe, coef = solve(float(alpha), y, sqrt_sw, *decomposition)
            if self.scoring is None:
                squared_errors = looe**2
                alpha_score = self._score_without_scorer(squared_errors=squared_errors)
                if self.store_cv_results:
                    self.cv_results_[:, i] = _ravel(squared_errors)
            else:
                predictions = y - looe
                # Rescale predictions back to original scale
                if sample_weight is not None:  # avoid the unnecessary division by ones
                    if predictions.ndim > 1:
                        predictions /= sqrt_sw[:, None]
                    else:
                        predictions /= sqrt_sw
                predictions += y_offset

                if self.store_cv_results:
                    self.cv_results_[:, i] = _ravel(predictions)

                score_params = score_params or {}
                alpha_score = self._score(
                    predictions=predictions,
                    y=unscaled_y,
                    n_y=n_y,
                    scorer=self.scoring,
                    score_params=score_params,
                )

            # Keep track of the best model
            if best_score is None:
                # initialize
                if self.alpha_per_target and n_y > 1:
                    best_coef = coef
                    best_score = xp.reshape(alpha_score, shape=(-1,))
                    best_alpha = xp.full(n_y, alpha, device=device_)
                else:
                    best_coef = coef
                    best_score = alpha_score
                    best_alpha = alpha
            else:
                # update
                if self.alpha_per_target and n_y > 1:
                    to_update = alpha_score > best_score
                    best_coef[:, to_update] = coef[:, to_update]
                    best_score[to_update] = alpha_score[to_update]
                    best_alpha[to_update] = alpha
                elif alpha_score > best_score:
                    best_coef, best_score, best_alpha = coef, alpha_score, alpha

        self.alpha_ = best_alpha
        self.best_score_ = best_score
        self.coef_ = best_coef
        if y.ndim == 2:
            self.coef_ = self.coef_.T
        if y.ndim == 1 or y.shape[1] == 1:
            self.coef_ = _ravel(self.coef_)

        self._set_intercept(X_offset, y_offset, X_scale)

        if self.store_cv_results:
            if y.ndim == 1:
                cv_results_shape = n_samples, n_alphas
            else:
                cv_results_shape = n_samples, n_y, n_alphas
            self.cv_results_ = xp.reshape(self.cv_results_, shape=cv_results_shape)

        if original_floating_dtype:
            if type(self.intercept_) is not float:
                self.intercept_ = xp.astype(
                    self.intercept_, original_floating_dtype, copy=False
                )
            self.coef_ = xp.astype(self.coef_, original_floating_dtype, copy=False)
            if self.store_cv_results:
                self.cv_results_ = xp.astype(
                    self.cv_results_, original_floating_dtype, copy=False
                )

        return self