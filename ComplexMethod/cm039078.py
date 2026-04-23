def fit(self, X, y=None):
        """Compute the median and quantiles to be used for scaling.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data used to compute the median and quantiles
            used for later scaling along the features axis.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted scaler.
        """
        # at fit, convert sparse matrices to csc for optimized computation of
        # the quantiles
        X = validate_data(
            self,
            X,
            accept_sparse="csc",
            dtype=FLOAT_DTYPES,
            ensure_all_finite="allow-nan",
        )

        q_min, q_max = self.quantile_range
        if not 0 <= q_min <= q_max <= 100:
            raise ValueError("Invalid quantile range: %s" % str(self.quantile_range))

        if self.with_centering:
            if sparse.issparse(X):
                raise ValueError(
                    "Cannot center sparse matrices: use `with_centering=False`"
                    " instead. See docstring for motivation and alternatives."
                )
            self.center_ = np.nanmedian(X, axis=0)
        else:
            self.center_ = None

        if self.with_scaling:
            quantiles = []
            for feature_idx in range(X.shape[1]):
                if sparse.issparse(X):
                    column_nnz_data = X.data[
                        X.indptr[feature_idx] : X.indptr[feature_idx + 1]
                    ]
                    column_data = np.zeros(shape=X.shape[0], dtype=X.dtype)
                    column_data[: len(column_nnz_data)] = column_nnz_data
                else:
                    column_data = X[:, feature_idx]

                quantiles.append(np.nanpercentile(column_data, self.quantile_range))

            quantiles = np.transpose(quantiles)

            self.scale_ = quantiles[1] - quantiles[0]
            self.scale_ = _handle_zeros_in_scale(self.scale_, copy=False)
            if self.unit_variance:
                adjust = stats.norm.ppf(q_max / 100.0) - stats.norm.ppf(q_min / 100.0)
                self.scale_ = self.scale_ / adjust
        else:
            self.scale_ = None

        return self