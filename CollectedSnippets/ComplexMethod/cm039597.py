def fit(self, X, y, sample_weight=None, check_input=True):
        """Fit model with coordinate descent.

        Parameters
        ----------
        X : {ndarray, sparse matrix, sparse array} of shape (n_samples, n_features)
            Data.

            Note that large sparse matrices and arrays requiring `int64`
            indices are not accepted.

        y : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Target. Will be cast to X's dtype if necessary.

        sample_weight : float or array-like of shape (n_samples,), default=None
            Sample weights. Internally, the `sample_weight` vector will be
            rescaled to sum to `n_samples`.

            .. versionadded:: 0.23

        check_input : bool, default=True
            Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        Returns
        -------
        self : object
            Fitted estimator.

        Notes
        -----
        Coordinate descent is an algorithm that considers each column of
        data at a time hence it will automatically convert the X input
        as a Fortran-contiguous numpy array if necessary.

        To avoid memory re-allocation it is advised to allocate the
        initial data in memory directly using that format.
        """
        if self.alpha == 0:
            warnings.warn(
                (
                    "With alpha=0, this algorithm does not converge "
                    "well. You are advised to use the LinearRegression "
                    "estimator"
                ),
                stacklevel=2,
            )

        # Remember if X is copied
        X_copied = False
        # We expect X and y to be float64 or float32 Fortran ordered arrays
        # when bypassing checks
        if check_input:
            X_copied = self.copy_X and self.fit_intercept
            X, y = validate_data(
                self,
                X,
                y,
                accept_sparse="csc",
                order="F",
                dtype=[np.float64, np.float32],
                force_writeable=True,
                accept_large_sparse=False,
                copy=X_copied,
                multi_output=True,
                y_numeric=True,
            )
            y = check_array(
                y, order="F", copy=False, dtype=X.dtype.type, ensure_2d=False
            )

        n_samples, n_features = X.shape

        if isinstance(sample_weight, numbers.Number):
            sample_weight = None
        if sample_weight is not None:
            if check_input:
                sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)
            # TLDR: Rescale sw to sum up to n_samples.
            # Long: The objective function of Enet
            #
            #    1/2 * np.average(squared error, weights=sw)
            #    + alpha * penalty                                             (1)
            #
            # is invariant under rescaling of sw.
            # But enet_path coordinate descent minimizes
            #
            #     1/2 * sum(squared error) + alpha' * penalty                  (2)
            #
            # and therefore sets
            #
            #     alpha' = n_samples * alpha                                   (3)
            #
            # inside its function body, which results in objective (2) being
            # equivalent to (1) in case of no sw.
            # With sw, however, enet_path should set
            #
            #     alpha' = sum(sw) * alpha                                     (4)
            #
            # Therefore, we use the freedom of Eq. (1) to rescale sw before
            # calling enet_path, i.e.
            #
            #     sw *= n_samples / sum(sw)
            #
            # such that sum(sw) = n_samples. This way, (3) and (4) are the same.
            sample_weight = sample_weight * (n_samples / np.sum(sample_weight))
            # Note: Alternatively, we could also have rescaled alpha instead
            # of sample_weight:
            #
            #     alpha *= np.sum(sample_weight) / n_samples

        # Ensure copying happens only once, don't do it again if done above.
        # X and y will be rescaled if sample_weight is not None, order='F'
        # ensures that the returned X and y are still F-contiguous.
        should_copy = self.copy_X and not X_copied
        X, y, X_offset, y_offset, X_scale, precompute, Xy = _pre_fit(
            X,
            y,
            None,
            self.precompute,
            fit_intercept=self.fit_intercept,
            copy=should_copy,
            check_gram=check_input,
            sample_weight=sample_weight,
        )
        # coordinate descent needs F-ordered arrays and _pre_fit might have
        # called _rescale_data
        if check_input or sample_weight is not None:
            X, y = _set_order(X, y, order="F")
        if y.ndim == 1:
            y = y[:, np.newaxis]
        if Xy is not None and Xy.ndim == 1:
            Xy = Xy[:, np.newaxis]

        n_targets = y.shape[1]

        if not self.warm_start or not hasattr(self, "coef_"):
            coef_ = np.zeros((n_targets, n_features), dtype=X.dtype, order="F")
        else:
            coef_ = self.coef_
            if coef_.ndim == 1:
                coef_ = coef_[np.newaxis, :]

        dual_gaps_ = np.zeros(n_targets, dtype=X.dtype)
        self.n_iter_ = []

        for k in range(n_targets):
            if Xy is not None:
                this_Xy = Xy[:, k]
            else:
                this_Xy = None
            _, this_coef, this_dual_gap, this_iter = self.path(
                X,
                y[:, k],
                l1_ratio=self.l1_ratio,
                eps=None,
                n_alphas=None,
                alphas=[self.alpha],
                precompute=precompute,
                Xy=this_Xy,
                copy_X=True,
                coef_init=coef_[k],
                verbose=False,
                return_n_iter=True,
                positive=self.positive,
                check_input=False,
                # from here on **params
                tol=self.tol,
                X_offset=X_offset,
                X_scale=X_scale,
                max_iter=self.max_iter,
                random_state=self.random_state,
                selection=self.selection,
                sample_weight=sample_weight,
            )
            coef_[k] = this_coef[:, 0]
            dual_gaps_[k] = this_dual_gap[0]
            self.n_iter_.append(this_iter[0])

        if n_targets == 1:
            self.n_iter_ = self.n_iter_[0]
            self.coef_ = coef_[0]
            self.dual_gap_ = dual_gaps_[0]
        else:
            self.coef_ = coef_
            self.dual_gap_ = dual_gaps_

        self._set_intercept(X_offset, y_offset, X_scale)

        # check for finiteness of coefficients
        if not all(np.isfinite(w).all() for w in [self.coef_, self.intercept_]):
            raise ValueError(
                "Coordinate descent iterations resulted in non-finite parameter"
                " values. The input data may contain large values and need to"
                " be preprocessed."
            )

        # return self for chaining fit and predict calls
        return self