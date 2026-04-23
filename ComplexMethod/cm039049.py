def fit(self, X, y, **fit_params):
        """Fit underlying estimators.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Data.

        y : array-like of shape (n_samples,)
            Multi-class targets.

        **fit_params : dict
            Parameters passed to the ``estimator.fit`` method of each
            sub-estimator.

            .. versionadded:: 1.4
                Only available if `enable_metadata_routing=True`. See
                :ref:`Metadata Routing User Guide <metadata_routing>` for more
                details.

        Returns
        -------
        self : object
            Returns a fitted instance of self.
        """
        _raise_for_params(fit_params, self, "fit")

        routed_params = process_routing(
            self,
            "fit",
            **fit_params,
        )

        y = validate_data(self, X="no_validation", y=y)

        random_state = check_random_state(self.random_state)
        check_classification_targets(y)

        self.classes_ = np.unique(y)
        n_classes = self.classes_.shape[0]
        if n_classes == 0:
            raise ValueError(
                "OutputCodeClassifier can not be fit when no class is present."
            )
        n_estimators = int(n_classes * self.code_size)

        # FIXME: there are more elaborate methods than generating the codebook
        # randomly.
        self.code_book_ = random_state.uniform(size=(n_classes, n_estimators))
        self.code_book_[self.code_book_ > 0.5] = 1.0

        if hasattr(self.estimator, "decision_function"):
            self.code_book_[self.code_book_ != 1] = -1.0
        else:
            self.code_book_[self.code_book_ != 1] = 0.0

        classes_index = {c: i for i, c in enumerate(self.classes_)}

        Y = np.array(
            [self.code_book_[classes_index[y[i]]] for i in range(_num_samples(y))],
            dtype=int,
        )

        self.estimators_ = Parallel(n_jobs=self.n_jobs)(
            delayed(_fit_binary)(
                self.estimator, X, Y[:, i], fit_params=routed_params.estimator.fit
            )
            for i in range(Y.shape[1])
        )

        if hasattr(self.estimators_[0], "n_features_in_"):
            self.n_features_in_ = self.estimators_[0].n_features_in_
        if hasattr(self.estimators_[0], "feature_names_in_"):
            self.feature_names_in_ = self.estimators_[0].feature_names_in_

        return self