def fit(self, X, y, sample_weight=None, **params):
        """Fit Ridge regression model with cv.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data. If using GCV, will be cast to float64
            if necessary.

        y : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Target values. Will be cast to X's dtype if necessary.

        sample_weight : float or ndarray of shape (n_samples,), default=None
            Individual weights for each sample. If given a float, every sample
            will have the same weight.

        **params : dict, default=None
            Extra parameters for the underlying scorer.

            .. versionadded:: 1.5
                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Fitted estimator.

        Notes
        -----
        When sample_weight is provided, the selected hyperparameter may depend
        on whether we use leave-one-out cross-validation (cv=None)
        or another form of cross-validation, because only leave-one-out
        cross-validation takes the sample weights into account when computing
        the validation score.
        """
        _raise_for_params(params, self, "fit")
        cv = self.cv
        scorer = self._get_scorer()

        # `_RidgeGCV` does not work for alpha = 0
        if cv is None:
            check_scalar_alpha = partial(
                check_scalar,
                target_type=numbers.Real,
                min_val=0.0,
                include_boundaries="neither",
            )
        else:
            check_scalar_alpha = partial(
                check_scalar,
                target_type=numbers.Real,
                min_val=0.0,
                include_boundaries="left",
            )

        if isinstance(self.alphas, (np.ndarray, list, tuple)):
            n_alphas = 1 if np.ndim(self.alphas) == 0 else len(self.alphas)
            if n_alphas != 1:
                for index, alpha in enumerate(self.alphas):
                    alpha = check_scalar_alpha(alpha, f"alphas[{index}]")
            else:
                self.alphas[0] = check_scalar_alpha(self.alphas[0], "alphas")
        alphas = np.asarray(self.alphas)

        if sample_weight is not None:
            params["sample_weight"] = sample_weight

        if cv is None:
            if _routing_enabled():
                routed_params = process_routing(
                    self,
                    "fit",
                    **params,
                )
            else:
                routed_params = Bunch(scorer=Bunch(score={}))
                if sample_weight is not None:
                    routed_params.scorer.score["sample_weight"] = sample_weight

            # reset `scorer` variable to original user-intend if no scoring is passed
            if self.scoring is None:
                scorer = None

            estimator = _RidgeGCV(
                alphas,
                fit_intercept=self.fit_intercept,
                scoring=scorer,
                gcv_mode=self.gcv_mode,
                store_cv_results=self.store_cv_results,
                is_clf=is_classifier(self),
                alpha_per_target=self.alpha_per_target,
            )
            estimator.fit(
                X,
                y,
                sample_weight=sample_weight,
                score_params=routed_params.scorer.score,
            )
            self.alpha_ = estimator.alpha_
            self.best_score_ = estimator.best_score_
            if self.store_cv_results:
                self.cv_results_ = estimator.cv_results_
        else:
            if self.store_cv_results:
                raise ValueError("cv!=None and store_cv_results=True are incompatible")
            if self.alpha_per_target:
                raise ValueError("cv!=None and alpha_per_target=True are incompatible")

            parameters = {"alpha": alphas}
            solver = "sparse_cg" if sparse.issparse(X) else "auto"
            model = RidgeClassifier if is_classifier(self) else Ridge
            estimator = model(
                fit_intercept=self.fit_intercept,
                solver=solver,
            )
            if _routing_enabled():
                estimator.set_fit_request(sample_weight=True)

            grid_search = GridSearchCV(
                estimator,
                parameters,
                cv=cv,
                scoring=scorer,
            )

            grid_search.fit(X, y, **params)
            estimator = grid_search.best_estimator_
            self.alpha_ = grid_search.best_estimator_.alpha
            self.best_score_ = grid_search.best_score_

        self.coef_ = estimator.coef_
        self.intercept_ = estimator.intercept_
        self.n_features_in_ = estimator.n_features_in_
        if hasattr(estimator, "feature_names_in_"):
            self.feature_names_in_ = estimator.feature_names_in_

        return self