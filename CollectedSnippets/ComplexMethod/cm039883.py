def fit(self, X, y, sample_weight=None, **fit_params):
        """Fit classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples, n_outputs) or (n_samples,), \
                default=None
            Target relative to X for classification or regression;
            None for unsupervised learning.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights. If None, then samples are equally weighted.

        **fit_params : dict of string -> object
            Parameters passed to the ``fit`` method of the estimator

        Returns
        -------
        self
        """
        assert _num_samples(X) == _num_samples(y)
        if self.methods_to_check == "all" or "fit" in self.methods_to_check:
            X, y = self._check_X_y(X, y, should_be_fitted=False)
        self.n_features_in_ = np.shape(X)[1]
        self.classes_ = np.unique(check_array(y, ensure_2d=False, allow_nd=True))
        if self.expected_fit_params:
            missing = set(self.expected_fit_params) - set(fit_params)
            if missing:
                raise AssertionError(
                    f"Expected fit parameter(s) {list(missing)} not seen."
                )
            for key, value in fit_params.items():
                if _num_samples(value) != _num_samples(X):
                    raise AssertionError(
                        f"Fit parameter {key} has length {_num_samples(value)}"
                        f"; expected {_num_samples(X)}."
                    )
        if self.expected_sample_weight:
            if sample_weight is None:
                raise AssertionError("Expected sample_weight to be passed")
            _check_sample_weight(sample_weight, X)

        return self