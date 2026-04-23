def fit(self, X, y, **params):
        """Fit the RFE model and automatically tune the number of selected features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the total number of features.

        y : array-like of shape (n_samples,)
            Target values (integers for classification, real numbers for
            regression).

        **params : dict of str -> object
            Parameters passed to the ``fit`` method of the estimator,
            the scorer, and the CV splitter.

            .. versionadded:: 1.6
                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>`
                for more details.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        _raise_for_params(params, self, "fit", allow=["groups"])
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse="csr",
            ensure_min_features=2,
            ensure_all_finite=False,
            multi_output=True,
        )

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **params)
        else:
            routed_params = Bunch(
                estimator=Bunch(fit={}),
                splitter=Bunch(split={"groups": params.pop("groups", None)}),
                scorer=Bunch(score={}),
            )

        # Initialization
        cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))
        scorer = self._get_scorer()

        # Build an RFE object, which will evaluate and score each possible
        # feature count, down to self.min_features_to_select
        n_features = X.shape[1]
        if self.min_features_to_select > n_features:
            warnings.warn(
                (
                    f"Found min_features_to_select={self.min_features_to_select} > "
                    f"{n_features=}. There will be no feature selection and all "
                    "features will be kept."
                ),
                UserWarning,
            )
        rfe = RFE(
            estimator=self.estimator,
            n_features_to_select=min(self.min_features_to_select, n_features),
            importance_getter=self.importance_getter,
            step=self.step,
            verbose=self.verbose,
        )

        # Determine the number of subsets of features by fitting across
        # the train folds and choosing the "features_to_select" parameter
        # that gives the least averaged error across all folds.

        # Note that joblib raises a non-picklable error for bound methods
        # even if n_jobs is set to 1 with the default multiprocessing
        # backend.
        # This branching is done so that to
        # make sure that user code that sets n_jobs to 1
        # and provides bound methods as scorers is not broken with the
        # addition of n_jobs parameter in version 0.18.

        if effective_n_jobs(self.n_jobs) == 1:
            parallel, func = list, _rfe_single_fit
        else:
            parallel = Parallel(n_jobs=self.n_jobs)
            func = delayed(_rfe_single_fit)

        step_results = parallel(
            func(clone(rfe), self.estimator, X, y, train, test, scorer, routed_params)
            for train, test in cv.split(X, y, **routed_params.splitter.split)
        )
        scores, supports, rankings, step_n_features = zip(*step_results)

        step_n_features_rev = np.array(step_n_features[0])[::-1]
        scores = np.array(scores)
        rankings = np.array(rankings)
        supports = np.array(supports)

        # Reverse order such that lowest number of features is selected in case of tie.
        scores_sum_rev = np.sum(scores, axis=0)[::-1]
        n_features_to_select = step_n_features_rev[np.argmax(scores_sum_rev)]

        # Re-execute an elimination with best_k over the whole set
        rfe = RFE(
            estimator=self.estimator,
            n_features_to_select=n_features_to_select,
            step=self.step,
            importance_getter=self.importance_getter,
            verbose=self.verbose,
        )

        rfe.fit(X, y, **routed_params.estimator.fit)

        # Set final attributes
        self.support_ = rfe.support_
        self.n_features_ = rfe.n_features_
        self.ranking_ = rfe.ranking_
        self.estimator_ = clone(self.estimator)
        self.estimator_.fit(self._transform(X), y, **routed_params.estimator.fit)

        # reverse to stay consistent with before
        scores_rev = scores[:, ::-1]
        supports_rev = supports[:, ::-1]
        rankings_rev = rankings[:, ::-1]
        self.cv_results_ = {
            "mean_test_score": np.mean(scores_rev, axis=0),
            "std_test_score": np.std(scores_rev, axis=0),
            **{f"split{i}_test_score": scores_rev[i] for i in range(scores.shape[0])},
            **{f"split{i}_ranking": rankings_rev[i] for i in range(rankings.shape[0])},
            **{f"split{i}_support": supports_rev[i] for i in range(supports.shape[0])},
            "n_features": step_n_features_rev,
        }
        return self