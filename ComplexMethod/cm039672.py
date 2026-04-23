def _fit(self, X, y, **params):
        """Fit the classifier and post-tune the decision threshold.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,)
            Target values.

        **params : dict
            Parameters to pass to the `fit` method of the underlying
            classifier and to the `scoring` scorer.

        Returns
        -------
        self : object
            Returns an instance of self.
        """
        if isinstance(self.cv, Real) and 0 < self.cv < 1:
            cv = StratifiedShuffleSplit(
                n_splits=1, test_size=self.cv, random_state=self.random_state
            )
        elif self.cv == "prefit":
            if self.refit is True:
                raise ValueError("When cv='prefit', refit cannot be True.")
            try:
                check_is_fitted(self.estimator, "classes_")
            except NotFittedError as exc:
                raise NotFittedError(
                    """When cv='prefit', `estimator` must be fitted."""
                ) from exc
            cv = self.cv
        else:
            cv = check_cv(self.cv, y=y, classifier=True)
            if self.refit is False and cv.get_n_splits() > 1:
                raise ValueError("When cv has several folds, refit cannot be False.")

        routed_params = process_routing(self, "fit", **params)
        self._curve_scorer = self._get_curve_scorer()

        # in the following block, we:
        # - define the final classifier `self.estimator_` and train it if necessary
        # - define `classifier` to be used to post-tune the decision threshold
        # - define `split` to be used to fit/score `classifier`
        if cv == "prefit":
            self.estimator_ = self.estimator
            classifier = self.estimator_
            splits = [(None, range(_num_samples(X)))]
        else:
            self.estimator_ = clone(self.estimator)
            classifier = clone(self.estimator)
            splits = cv.split(X, y, **routed_params.splitter.split)

            if self.refit:
                # train on the whole dataset
                X_train, y_train, fit_params_train = X, y, routed_params.estimator.fit
            else:
                # single split cross-validation
                train_idx, _ = next(cv.split(X, y, **routed_params.splitter.split))
                X_train = _safe_indexing(X, train_idx)
                y_train = _safe_indexing(y, train_idx)
                fit_params_train = _check_method_params(
                    X, routed_params.estimator.fit, indices=train_idx
                )

            self.estimator_.fit(X_train, y_train, **fit_params_train)

        cv_scores, cv_thresholds = zip(
            *Parallel(n_jobs=self.n_jobs)(
                delayed(_fit_and_score_over_thresholds)(
                    clone(classifier) if cv != "prefit" else classifier,
                    X,
                    y,
                    fit_params=routed_params.estimator.fit,
                    train_idx=train_idx,
                    val_idx=val_idx,
                    curve_scorer=self._curve_scorer,
                    score_params=routed_params.scorer.score,
                )
                for train_idx, val_idx in splits
            )
        )

        if any(np.isclose(th[0], th[-1]) for th in cv_thresholds):
            raise ValueError(
                "The provided estimator makes constant predictions. Therefore, it is "
                "impossible to optimize the decision threshold."
            )

        # find the global min and max thresholds across all folds
        min_threshold = min(
            split_thresholds.min() for split_thresholds in cv_thresholds
        )
        max_threshold = max(
            split_thresholds.max() for split_thresholds in cv_thresholds
        )
        if isinstance(self.thresholds, Integral):
            decision_thresholds = np.linspace(
                min_threshold, max_threshold, num=self.thresholds
            )
        else:
            decision_thresholds = np.asarray(self.thresholds)

        objective_scores = _mean_interpolated_score(
            decision_thresholds, cv_thresholds, cv_scores
        )
        best_idx = objective_scores.argmax()
        self.best_score_ = objective_scores[best_idx]
        self.best_threshold_ = decision_thresholds[best_idx]
        if self.store_cv_results:
            self.cv_results_ = {
                "thresholds": decision_thresholds,
                "scores": objective_scores,
            }

        return self