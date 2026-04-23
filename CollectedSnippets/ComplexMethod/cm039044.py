def fit(self, X, y, sample_weight=None):
        """Fit the baseline classifier.

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
            Returns the instance itself.
        """
        validate_data(self, X, skip_check_array=True)

        self._strategy = self.strategy

        if self._strategy == "uniform" and sp.issparse(y):
            y = y.toarray()
            warnings.warn(
                (
                    "A local copy of the target data has been converted "
                    "to a numpy array. Predicting on sparse target data "
                    "with the uniform strategy would not save memory "
                    "and would be slower."
                ),
                UserWarning,
            )

        self.sparse_output_ = sp.issparse(y)

        if not self.sparse_output_:
            y = np.asarray(y)
            y = np.atleast_1d(y)

        if y.ndim == 1:
            y = np.reshape(y, (-1, 1))

        self.n_outputs_ = y.shape[1]

        check_consistent_length(X, y)

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X)

        if self._strategy == "constant":
            if self.constant is None:
                raise ValueError(
                    "Constant target value has to be specified "
                    "when the constant strategy is used."
                )
            else:
                constant = np.reshape(np.atleast_1d(self.constant), (-1, 1))
                if constant.shape[0] != self.n_outputs_:
                    raise ValueError(
                        "Constant target value should have shape (%d, 1)."
                        % self.n_outputs_
                    )

        (self.classes_, self.n_classes_, self.class_prior_) = class_distribution(
            y, sample_weight
        )

        if self._strategy == "constant":
            for k in range(self.n_outputs_):
                if not any(constant[k][0] == c for c in self.classes_[k]):
                    # Checking in case of constant strategy if the constant
                    # provided by the user is in y.
                    err_msg = (
                        "The constant target value must be present in "
                        "the training data. You provided constant={}. "
                        "Possible values are: {}.".format(
                            self.constant, self.classes_[k].tolist()
                        )
                    )
                    raise ValueError(err_msg)

        if self.n_outputs_ == 1:
            self.n_classes_ = self.n_classes_[0]
            self.classes_ = self.classes_[0]
            self.class_prior_ = self.class_prior_[0]

        return self