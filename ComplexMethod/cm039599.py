def fit(self, X, y, sample_weight=None):
        """Fit MultiTaskElasticNet model with coordinate descent.

        Parameters
        ----------
        X : {ndarray, sparse matrix, sparse array} of shape (n_samples, n_features)
            Data. Pass directly as Fortran-contiguous data to avoid unnecessary memory
            duplication.

            Note that large sparse matrices and arrays requiring `int64`
            indices are not accepted.

        y : ndarray of shape (n_samples, n_targets)
            Target. Will be cast to X's dtype if necessary.

        sample_weight : float or array-like of shape (n_samples,), default=None
            Sample weights. Internally, the `sample_weight` vector will be
            rescaled to sum to `n_samples`.

            .. versionadded:: 1.9

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
        # Remember if X is copied
        X_copied = self.copy_X and self.fit_intercept
        # Need to validate separately here.
        # We can't pass multi_output=True because that would allow y to be csr.
        check_X_params = dict(
            accept_sparse="csc",
            dtype=[np.float64, np.float32],
            order="F",
            force_writeable=True,
            accept_large_sparse=False,
            copy=X_copied,
        )
        check_y_params = dict(
            copy=False, dtype=[np.float64, np.float32], ensure_2d=False, order="F"
        )
        X, y = validate_data(
            self, X, y, validate_separately=(check_X_params, check_y_params)
        )
        check_consistent_length(X, y)

        if y.ndim == 1:
            if hasattr(self, "l1_ratio"):
                model_str = "ElasticNet"
            else:
                model_str = "Lasso"
            raise ValueError("For mono-task outputs, use %s" % model_str)

        n_samples, n_features = X.shape
        n_targets = y.shape[1]

        if isinstance(sample_weight, numbers.Number):
            sample_weight = None
        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)
            # TLDR: Rescale sw to sum up to n_samples.
            # Long: See comment in ElasticNet.
            sample_weight = sample_weight * (n_samples / np.sum(sample_weight))

        X, y, X_offset, y_offset, X_scale, _, _ = _pre_fit(
            X=X,
            y=y,
            Xy=None,
            precompute=False,
            fit_intercept=self.fit_intercept,
            copy=False,  # TODO: improve
            sample_weight=sample_weight,
        )
        # coordinate descent needs F-ordered arrays and _pre_fit might have
        # called _rescale_data
        if sample_weight is not None:
            X, y = _set_order(X, y, order="F")

        if not self.warm_start or not hasattr(self, "coef_"):
            self.coef_ = np.zeros((n_targets, n_features), dtype=X.dtype, order="F")
        else:
            self.coef_ = np.asfortranarray(self.coef_)  # coef F-contiguous in memory

        X_is_sparse = sparse.issparse(X)
        if X_is_sparse:
            X_data = X.data
            X_indices = X.indices
            X_indptr = X.indptr
            # As sparse matrices are not actually centered we need this to be passed to
            # the CD solver.
            X_mean = np.asarray(X_offset / X_scale, dtype=X.dtype)
            X = None
        else:
            X_data = None
            X_indices = None
            X_indptr = None
            X_mean = None

        # account for n_samples scaling in objectives between here and cd_fast
        l1_reg = self.alpha * self.l1_ratio * n_samples
        l2_reg = self.alpha * (1.0 - self.l1_ratio) * n_samples

        (
            self.coef_,
            self.dual_gap_,
            self.eps_,
            self.n_iter_,
        ) = cd_fast.enet_coordinate_descent_multi_task(
            W=self.coef_,
            alpha=l1_reg,
            beta=l2_reg,
            X=X,
            X_is_sparse=X_is_sparse,
            X_data=X_data,
            X_indices=X_indices,
            X_indptr=X_indptr,
            Y=y,
            sample_weight=sample_weight,
            X_mean=X_mean,
            max_iter=self.max_iter,
            tol=self.tol,
            rng=check_random_state(self.random_state),
            random=self.selection == "random",
            do_screening=True,
        )

        # account for different objective scaling here and in cd_fast
        self.dual_gap_ /= n_samples

        self._set_intercept(X_offset, y_offset, X_scale)

        # return self for chaining fit and predict calls
        return self