def fit(self, X, y, sample_weight=None):
        """Fit the baseline regressor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,) or (n_samples, n_outputs)
            Target values.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        validate_data(self, X, skip_check_array=True)

        y = check_array(y, ensure_2d=False, input_name="y")
        if len(y) == 0:
            raise ValueError("y must not be empty.")

        if y.ndim == 1:
            y = np.reshape(y, (-1, 1))
        self.n_outputs_ = y.shape[1]

        check_consistent_length(X, y, sample_weight)

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X)

        if self.strategy == "mean":
            self.constant_ = np.average(y, axis=0, weights=sample_weight)

        elif self.strategy == "median":
            if sample_weight is None:
                self.constant_ = np.median(y, axis=0)
            else:
                self.constant_ = _weighted_percentile(
                    y, sample_weight, percentile_rank=50.0
                )

        elif self.strategy == "quantile":
            if self.quantile is None:
                raise ValueError(
                    "When using `strategy='quantile', you have to specify the desired "
                    "quantile in the range [0, 1]."
                )
            percentile_rank = self.quantile * 100.0
            if sample_weight is None:
                self.constant_ = np.percentile(y, axis=0, q=percentile_rank)
            else:
                self.constant_ = _weighted_percentile(
                    y, sample_weight, percentile_rank=percentile_rank
                )

        elif self.strategy == "constant":
            if self.constant is None:
                raise TypeError(
                    "Constant target value has to be specified "
                    "when the constant strategy is used."
                )

            self.constant_ = check_array(
                self.constant,
                accept_sparse=["csr", "csc", "coo"],
                ensure_2d=False,
                ensure_min_samples=0,
            )

            if self.n_outputs_ != 1 and self.constant_.shape[0] != y.shape[1]:
                raise ValueError(
                    "Constant target value should have shape (%d, 1)." % y.shape[1]
                )

        self.constant_ = np.reshape(self.constant_, (1, -1))
        return self