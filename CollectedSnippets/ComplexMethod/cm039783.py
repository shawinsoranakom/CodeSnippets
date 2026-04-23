def fit(self, X, y, **params):
        """
        Fit self-training classifier using `X`, `y` as training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Array representing the data.

        y : {array-like, sparse matrix} of shape (n_samples,)
            Array representing the labels. Unlabeled samples should have the
            label -1.

        **params : dict
            Parameters to pass to the underlying estimators.

            .. versionadded:: 1.6
                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        _raise_for_params(params, self, "fit")

        self.estimator_ = self._get_estimator()

        # we need row slicing support for sparse matrices, but costly finiteness check
        # can be delegated to the base estimator.
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csr", "csc", "lil", "dok"],
            ensure_all_finite=False,
        )

        if y.dtype.kind in ["U", "S"]:
            raise ValueError(
                "y has dtype string. If you wish to predict on "
                "string targets, use dtype object, and use -1"
                " as the label for unlabeled samples."
            )

        has_label = y != -1

        if np.all(has_label):
            warnings.warn("y contains no unlabeled samples", UserWarning)

        if self.criterion == "k_best" and (
            self.k_best > X.shape[0] - np.sum(has_label)
        ):
            warnings.warn(
                (
                    "k_best is larger than the amount of unlabeled "
                    "samples. All unlabeled samples will be labeled in "
                    "the first iteration"
                ),
                UserWarning,
            )

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **params)
        else:
            routed_params = Bunch(estimator=Bunch(fit={}))

        self.transduction_ = np.copy(y)
        self.labeled_iter_ = np.full_like(y, -1)
        self.labeled_iter_[has_label] = 0

        self.n_iter_ = 0

        while not np.all(has_label) and (
            self.max_iter is None or self.n_iter_ < self.max_iter
        ):
            self.n_iter_ += 1
            self.estimator_.fit(
                X[safe_mask(X, has_label)],
                self.transduction_[has_label],
                **routed_params.estimator.fit,
            )

            # Predict on the unlabeled samples
            prob = self.estimator_.predict_proba(X[safe_mask(X, ~has_label)])
            pred = self.estimator_.classes_[np.argmax(prob, axis=1)]
            max_proba = np.max(prob, axis=1)

            # Select new labeled samples
            if self.criterion == "threshold":
                selected = max_proba > self.threshold
            else:
                n_to_select = min(self.k_best, max_proba.shape[0])
                if n_to_select == max_proba.shape[0]:
                    selected = np.ones_like(max_proba, dtype=bool)
                else:
                    # NB these are indices, not a mask
                    selected = np.argpartition(-max_proba, n_to_select)[:n_to_select]

            # Map selected indices into original array
            selected_full = np.nonzero(~has_label)[0][selected]

            # Add newly labeled confident predictions to the dataset
            self.transduction_[selected_full] = pred[selected]
            has_label[selected_full] = True
            self.labeled_iter_[selected_full] = self.n_iter_

            if selected_full.shape[0] == 0:
                # no changed labels
                self.termination_condition_ = "no_change"
                break

            if self.verbose:
                print(
                    f"End of iteration {self.n_iter_},"
                    f" added {selected_full.shape[0]} new labels."
                )

        if self.n_iter_ == self.max_iter:
            self.termination_condition_ = "max_iter"
        if np.all(has_label):
            self.termination_condition_ = "all_labeled"

        self.estimator_.fit(
            X[safe_mask(X, has_label)],
            self.transduction_[has_label],
            **routed_params.estimator.fit,
        )
        self.classes_ = self.estimator_.classes_
        return self