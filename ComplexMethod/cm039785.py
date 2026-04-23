def fit(self, X, y):
        """Fit Gaussian process classification model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features) or list of object
            Feature vectors or other representations of training data.

        y : array-like of shape (n_samples,)
            Target values, must be binary.

        Returns
        -------
        self : object
            Returns an instance of self.
        """
        if isinstance(self.kernel, CompoundKernel):
            raise ValueError("kernel cannot be a CompoundKernel")

        if self.kernel is None or self.kernel.requires_vector_input:
            X, y = validate_data(
                self, X, y, multi_output=False, ensure_2d=True, dtype="numeric"
            )
        else:
            X, y = validate_data(
                self, X, y, multi_output=False, ensure_2d=False, dtype=None
            )

        self.base_estimator_ = _BinaryGaussianProcessClassifierLaplace(
            kernel=self.kernel,
            optimizer=self.optimizer,
            n_restarts_optimizer=self.n_restarts_optimizer,
            max_iter_predict=self.max_iter_predict,
            warm_start=self.warm_start,
            copy_X_train=self.copy_X_train,
            random_state=self.random_state,
        )

        self.classes_ = np.unique(y)
        self.n_classes_ = self.classes_.size
        if self.n_classes_ == 1:
            raise ValueError(
                "GaussianProcessClassifier requires 2 or more "
                "distinct classes; got %d class (only class %s "
                "is present)" % (self.n_classes_, self.classes_[0])
            )
        if self.n_classes_ > 2:
            if self.multi_class == "one_vs_rest":
                self.base_estimator_ = OneVsRestClassifier(
                    self.base_estimator_, n_jobs=self.n_jobs
                )
            elif self.multi_class == "one_vs_one":
                self.base_estimator_ = OneVsOneClassifier(
                    self.base_estimator_, n_jobs=self.n_jobs
                )
            else:
                raise ValueError("Unknown multi-class mode %s" % self.multi_class)

        self.base_estimator_.fit(X, y)

        if self.n_classes_ > 2:
            self.log_marginal_likelihood_value_ = np.mean(
                [
                    estimator.log_marginal_likelihood()
                    for estimator in self.base_estimator_.estimators_
                ]
            )
        else:
            self.log_marginal_likelihood_value_ = (
                self.base_estimator_.log_marginal_likelihood()
            )

        return self