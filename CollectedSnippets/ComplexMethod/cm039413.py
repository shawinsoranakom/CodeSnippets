def fit(self, X, y, **fit_params):
        """Fit the estimators.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vectors, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target values.

        **fit_params : dict
            Dict of metadata, potentially containing sample_weight as a
            key-value pair. If sample_weight is not present, then samples are
            equally weighted. Note that sample_weight is supported only if all
            underlying estimators support sample weights.

            .. versionadded:: 1.6

        Returns
        -------
        self : object
        """
        # all_estimators contains all estimators, the one to be fitted and the
        # 'drop' string.
        names, all_estimators = self._validate_estimators()
        self._validate_final_estimator()

        stack_method = [self.stack_method] * len(all_estimators)

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **fit_params)
        else:
            routed_params = Bunch()
            for name in names:
                routed_params[name] = Bunch(fit={})
                if "sample_weight" in fit_params:
                    routed_params[name].fit["sample_weight"] = fit_params[
                        "sample_weight"
                    ]

        if self.cv == "prefit":
            self.estimators_ = []
            for estimator in all_estimators:
                if estimator != "drop":
                    check_is_fitted(estimator)
                    self.estimators_.append(estimator)
        else:
            # Fit the base estimators on the whole training data. Those
            # base estimators will be used in transform, predict, and
            # predict_proba. They are exposed publicly.
            self.estimators_ = Parallel(n_jobs=self.n_jobs)(
                delayed(_fit_single_estimator)(
                    clone(est), X, y, routed_params[name]["fit"]
                )
                for name, est in zip(names, all_estimators)
                if est != "drop"
            )

        self.named_estimators_ = Bunch()
        est_fitted_idx = 0
        for name_est, org_est in zip(names, all_estimators):
            if org_est != "drop":
                current_estimator = self.estimators_[est_fitted_idx]
                self.named_estimators_[name_est] = current_estimator
                est_fitted_idx += 1
                if hasattr(current_estimator, "feature_names_in_"):
                    self.feature_names_in_ = current_estimator.feature_names_in_
            else:
                self.named_estimators_[name_est] = "drop"

        self.stack_method_ = [
            self._method_name(name, est, meth)
            for name, est, meth in zip(names, all_estimators, stack_method)
        ]

        if self.cv == "prefit":
            # Generate predictions from prefit models
            predictions = [
                getattr(estimator, predict_method)(X)
                for estimator, predict_method in zip(all_estimators, self.stack_method_)
                if estimator != "drop"
            ]
        else:
            # To train the meta-classifier using the most data as possible, we use
            # a cross-validation to obtain the output of the stacked estimators.
            # To ensure that the data provided to each estimator are the same,
            # we need to set the random state of the cv if there is one and we
            # need to take a copy.
            cv = check_cv(self.cv, y=y, classifier=is_classifier(self))
            if hasattr(cv, "random_state") and cv.random_state is None:
                cv.random_state = np.random.RandomState()

            predictions = Parallel(n_jobs=self.n_jobs)(
                delayed(cross_val_predict)(
                    clone(est),
                    X,
                    y,
                    cv=deepcopy(cv),
                    method=meth,
                    n_jobs=self.n_jobs,
                    params=routed_params[name]["fit"],
                    verbose=self.verbose,
                )
                for name, est, meth in zip(names, all_estimators, self.stack_method_)
                if est != "drop"
            )

        # Only not None or not 'drop' estimators will be used in transform.
        # Remove the None from the method as well.
        self.stack_method_ = [
            meth
            for (meth, est) in zip(self.stack_method_, all_estimators)
            if est != "drop"
        ]

        X_meta = self._concatenate_predictions(X, predictions)
        _fit_single_estimator(self.final_estimator_, X_meta, y, fit_params=fit_params)

        return self