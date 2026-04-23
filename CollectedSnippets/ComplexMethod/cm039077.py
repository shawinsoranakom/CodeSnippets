def partial_fit(self, X, y=None, sample_weight=None):
        """Online computation of mean and std on X for later scaling.

        All of X is processed as a single batch. This is intended for cases
        when :meth:`fit` is not feasible due to very large number of
        `n_samples` or because X is read from a continuous stream.

        The algorithm for incremental mean and std is given in Equation 1.5a,b
        in Chan, Tony F., Gene H. Golub, and Randall J. LeVeque. "Algorithms
        for computing the sample variance: Analysis and recommendations."
        The American Statistician 37.3 (1983): 242-247:

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data used to compute the mean and standard deviation
            used for later scaling along the features axis.

        y : None
            Ignored.

        sample_weight : array-like of shape (n_samples,), default=None
            Individual weights for each sample.

            .. versionadded:: 0.24
               parameter *sample_weight* support to StandardScaler.

        Returns
        -------
        self : object
            Fitted scaler.
        """
        xp, _, X_device = get_namespace_and_device(X)
        first_call = not hasattr(self, "n_samples_seen_")
        X = validate_data(
            self,
            X,
            accept_sparse=("csr", "csc"),
            dtype=supported_float_dtypes(xp, X_device),
            ensure_all_finite="allow-nan",
            reset=first_call,
        )
        n_features = X.shape[1]

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        # Even in the case of `with_mean=False`, we update the mean anyway
        # This is needed for the incremental computation of the var
        # See incr_mean_variance_axis and _incremental_mean_variance_axis

        # if n_samples_seen_ is an integer (i.e. no missing values), we need to
        # transform it to an array of shape (n_features,) required by
        # incr_mean_variance_axis and _incremental_variance_axis
        dtype = xp.int64 if sample_weight is None else X.dtype
        if first_call:
            self.n_samples_seen_ = xp.zeros(n_features, dtype=dtype, device=X_device)
        elif size(self.n_samples_seen_) == 1:
            self.n_samples_seen_ = xp.repeat(self.n_samples_seen_, X.shape[1])
            self.n_samples_seen_ = xp.astype(self.n_samples_seen_, dtype, copy=False)

        if sparse.issparse(X):
            if self.with_mean:
                raise ValueError(
                    "Cannot center sparse matrices: pass `with_mean=False` "
                    "instead. See docstring for motivation and alternatives."
                )
            sparse_constructor = (
                sparse.csr_array if X.format == "csr" else sparse.csc_array
            )

            if self.with_std:
                # First pass
                if not hasattr(self, "scale_"):
                    self.mean_, self.var_, self.n_samples_seen_ = mean_variance_axis(
                        X, axis=0, weights=sample_weight, return_sum_weights=True
                    )
                # Next passes
                else:
                    (
                        self.mean_,
                        self.var_,
                        self.n_samples_seen_,
                    ) = incr_mean_variance_axis(
                        X,
                        axis=0,
                        last_mean=self.mean_,
                        last_var=self.var_,
                        last_n=self.n_samples_seen_,
                        weights=sample_weight,
                    )
                # We force the mean and variance to float64 for large arrays
                # See https://github.com/scikit-learn/scikit-learn/pull/12338
                self.mean_ = self.mean_.astype(np.float64, copy=False)
                self.var_ = self.var_.astype(np.float64, copy=False)
            else:
                self.mean_ = None  # as with_mean must be False for sparse
                self.var_ = None
                weights = _check_sample_weight(sample_weight, X)
                sum_weights_nan = weights @ sparse_constructor(
                    (np.isnan(X.data), X.indices, X.indptr), shape=X.shape
                )
                self.n_samples_seen_ += (np.sum(weights) - sum_weights_nan).astype(
                    dtype
                )
        else:
            # First pass
            if not hasattr(self, "scale_"):
                self.mean_ = 0.0
                if self.with_std:
                    self.var_ = 0.0
                else:
                    self.var_ = None

            if not self.with_mean and not self.with_std:
                self.mean_ = None
                self.var_ = None
                self.n_samples_seen_ += X.shape[0] - xp.isnan(X).sum(axis=0)

            else:
                self.mean_, self.var_, self.n_samples_seen_ = _incremental_mean_and_var(
                    X,
                    self.mean_,
                    self.var_,
                    self.n_samples_seen_,
                    sample_weight=sample_weight,
                )

        # for backward-compatibility, reduce n_samples_seen_ to an integer
        # if the number of samples is the same for each feature (i.e. no
        # missing values)
        if xp.max(self.n_samples_seen_) == xp.min(self.n_samples_seen_):
            self.n_samples_seen_ = self.n_samples_seen_[0]

        if self.with_std:
            # Extract the list of near constant features on the raw variances,
            # before taking the square root.
            constant_mask = _is_constant_feature(
                self.var_, self.mean_, self.n_samples_seen_
            )
            self.scale_ = _handle_zeros_in_scale(
                xp.sqrt(self.var_), copy=False, constant_mask=constant_mask
            )
        else:
            self.scale_ = None

        return self