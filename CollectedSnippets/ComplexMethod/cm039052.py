def fit(self, X, Y, **fit_params):
        """Fit the model to data matrix X and targets Y.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The input data.

        Y : array-like of shape (n_samples, n_classes)
            The target values.

        **fit_params : dict of string -> object
            Parameters passed to the `fit` method of each step.

            .. versionadded:: 0.23

        Returns
        -------
        self : object
            Returns a fitted instance.
        """
        X, Y = validate_data(self, X, Y, multi_output=True, accept_sparse=True)

        random_state = check_random_state(self.random_state)
        self.order_ = self.order
        if isinstance(self.order_, tuple):
            self.order_ = np.array(self.order_)

        if self.order_ is None:
            self.order_ = np.array(range(Y.shape[1]))
        elif isinstance(self.order_, str):
            if self.order_ == "random":
                self.order_ = random_state.permutation(Y.shape[1])
        elif sorted(self.order_) != list(range(Y.shape[1])):
            raise ValueError("invalid order")

        self.estimators_ = [clone(self.estimator) for _ in range(Y.shape[1])]

        if self.cv is None:
            Y_pred_chain = Y[:, self.order_]
            if sp.issparse(X):
                X_aug = sp.hstack((X, Y_pred_chain), format="lil")
                X_aug = X_aug.tocsr()
            else:
                X_aug = np.hstack((X, Y_pred_chain))

        elif sp.issparse(X):
            # TODO: remove this condition check when the minimum supported scipy version
            # doesn't support sparse matrices anymore
            if not sp.isspmatrix(X):
                # if `X` is a scipy sparse dok_array, we convert it to a sparse
                # coo_array format before hstacking, it's faster; see
                # https://github.com/scipy/scipy/issues/20060#issuecomment-1937007039:
                if X.format == "dok":
                    X = sp.coo_array(X)
                # in case that `X` is a sparse array we create `Y_pred_chain` as a
                # sparse array format:
                Y_pred_chain = sp.coo_array((X.shape[0], Y.shape[1]))
            else:
                Y_pred_chain = sp.coo_matrix((X.shape[0], Y.shape[1]))
            X_aug = sp.hstack((X, Y_pred_chain), format="lil")

        else:
            Y_pred_chain = np.zeros((X.shape[0], Y.shape[1]))
            X_aug = np.hstack((X, Y_pred_chain))

        del Y_pred_chain

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **fit_params)
        else:
            routed_params = Bunch(estimator=Bunch(fit=fit_params))

        if hasattr(self, "chain_method"):
            chain_method = _check_response_method(
                self.estimator,
                self.chain_method,
            ).__name__
            self.chain_method_ = chain_method
        else:
            # `RegressorChain` does not have a `chain_method` parameter
            chain_method = "predict"

        for chain_idx, estimator in enumerate(self.estimators_):
            message = self._log_message(
                estimator_idx=chain_idx + 1,
                n_estimators=len(self.estimators_),
                processing_msg=f"Processing order {self.order_[chain_idx]}",
            )
            y = Y[:, self.order_[chain_idx]]
            with _print_elapsed_time("Chain", message):
                estimator.fit(
                    X_aug[:, : (X.shape[1] + chain_idx)],
                    y,
                    **routed_params.estimator.fit,
                )

            if self.cv is not None and chain_idx < len(self.estimators_) - 1:
                col_idx = X.shape[1] + chain_idx
                cv_result = cross_val_predict(
                    self.estimator,
                    X_aug[:, :col_idx],
                    y=y,
                    cv=self.cv,
                    method=chain_method,
                )
                # `predict_proba` output is 2D, we use only output for classes[-1]
                if cv_result.ndim > 1:
                    cv_result = cv_result[:, 1]
                if sp.issparse(X_aug):
                    X_aug[:, col_idx] = np.expand_dims(cv_result, 1)
                else:
                    X_aug[:, col_idx] = cv_result

        return self