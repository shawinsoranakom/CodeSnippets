def fit(self, X, y, sample_weight=None):
        """
        Fit linear model.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target values. Will be cast to X's dtype if necessary.

        sample_weight : array-like of shape (n_samples,), default=None
            Individual weights for each sample.

            .. versionadded:: 0.17
               parameter *sample_weight* support to LinearRegression.

        Returns
        -------
        self : object
            Fitted Estimator.
        """
        n_jobs_ = self.n_jobs

        accept_sparse = False if self.positive else ["csr", "csc", "coo"]

        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=accept_sparse,
            y_numeric=True,
            multi_output=True,
            force_writeable=True,
        )

        has_sw = sample_weight is not None
        if has_sw:
            sample_weight = _check_sample_weight(
                sample_weight, X, dtype=X.dtype, ensure_non_negative=True
            )

        # Note that neither _rescale_data nor the rest of the fit method of
        # LinearRegression can benefit from in-place operations when X is a
        # sparse matrix. Therefore, let's not copy X when it is sparse.
        copy_X_in_preprocess_data = self.copy_X and not sp.issparse(X)

        X, y, X_offset, y_offset, _, sample_weight_sqrt = _preprocess_data(
            X,
            y,
            fit_intercept=self.fit_intercept,
            copy=copy_X_in_preprocess_data,
            sample_weight=sample_weight,
        )

        if self.positive:
            if y.ndim < 2:
                self.coef_ = optimize.nnls(X, y)[0]
            else:
                # scipy.optimize.nnls cannot handle y with shape (M, K)
                outs = Parallel(n_jobs=n_jobs_)(
                    delayed(optimize.nnls)(X, y[:, j]) for j in range(y.shape[1])
                )
                self.coef_ = np.vstack([out[0] for out in outs])
        elif sp.issparse(X):
            if has_sw:

                def matvec(b):
                    return X.dot(b) - sample_weight_sqrt * b.dot(X_offset)

                def rmatvec(b):
                    return X.T.dot(b) - X_offset * b.dot(sample_weight_sqrt)

            else:

                def matvec(b):
                    return X.dot(b) - b.dot(X_offset)

                def rmatvec(b):
                    return X.T.dot(b) - X_offset * b.sum()

            X_centered = sparse.linalg.LinearOperator(
                shape=X.shape, matvec=matvec, rmatvec=rmatvec
            )

            if y.ndim < 2:
                self.coef_ = lsqr(X_centered, y, atol=self.tol, btol=self.tol)[0]
            else:
                # sparse_lstsq cannot handle y with shape (M, K)
                outs = Parallel(n_jobs=n_jobs_)(
                    delayed(lsqr)(
                        X_centered, y[:, j].ravel(), atol=self.tol, btol=self.tol
                    )
                    for j in range(y.shape[1])
                )
                self.coef_ = np.vstack([out[0] for out in outs])
        else:
            self.coef_, _, self.rank_, self.singular_ = linalg.lstsq(
                X, y, cond=self.tol
            )
            self.coef_ = self.coef_.T

        if y.ndim == 1:
            self.coef_ = np.ravel(self.coef_)
        self._set_intercept(X_offset, y_offset)
        return self