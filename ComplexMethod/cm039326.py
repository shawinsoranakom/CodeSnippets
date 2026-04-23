def fit(self, X, y=None, **params):
        """Learn the features to select from X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vectors, where `n_samples` is the number of samples and
            `n_features` is the number of predictors.

        y : array-like of shape (n_samples,), default=None
            Target values. This parameter may be ignored for
            unsupervised learning.

        **params : dict, default=None
            Parameters to be passed to the underlying `estimator`, `cv`
            and `scorer` objects.

            .. versionadded:: 1.6

                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        _raise_for_params(params, self, "fit")
        tags = self.__sklearn_tags__()
        X = validate_data(
            self,
            X,
            accept_sparse="csc",
            ensure_min_features=2,
            ensure_all_finite=not tags.input_tags.allow_nan,
        )
        n_features = X.shape[1]

        if self.n_features_to_select == "auto":
            if self.tol is not None:
                # With auto feature selection, `n_features_to_select_` will be updated
                # to `support_.sum()` after features are selected.
                self.n_features_to_select_ = n_features - 1
            else:
                self.n_features_to_select_ = n_features // 2
        elif isinstance(self.n_features_to_select, Integral):
            if self.n_features_to_select >= n_features:
                raise ValueError("n_features_to_select must be < n_features.")
            self.n_features_to_select_ = self.n_features_to_select
        elif isinstance(self.n_features_to_select, Real):
            self.n_features_to_select_ = int(n_features * self.n_features_to_select)

        if self.tol is not None and self.tol < 0 and self.direction == "forward":
            raise ValueError(
                "tol must be strictly positive when doing forward selection"
            )

        cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))

        cloned_estimator = clone(self.estimator)

        # the current mask corresponds to the set of features:
        # - that we have already *selected* if we do forward selection
        # - that we have already *excluded* if we do backward selection
        current_mask = np.zeros(shape=n_features, dtype=bool)
        n_iterations = (
            self.n_features_to_select_
            if self.n_features_to_select == "auto" or self.direction == "forward"
            else n_features - self.n_features_to_select_
        )

        old_score = -np.inf
        is_auto_select = self.tol is not None and self.n_features_to_select == "auto"

        # We only need to verify the routing here and not use the routed params
        # because internally the actual routing will also take place inside the
        # `cross_val_score` function.
        if _routing_enabled():
            process_routing(self, "fit", **params)
        for _ in range(n_iterations):
            new_feature_idx, new_score = self._get_best_new_feature_score(
                cloned_estimator, X, y, cv, current_mask, **params
            )
            if is_auto_select and ((new_score - old_score) < self.tol):
                break

            old_score = new_score
            current_mask[new_feature_idx] = True

        if self.direction == "backward":
            current_mask = ~current_mask

        self.support_ = current_mask
        self.n_features_to_select_ = self.support_.sum()

        return self