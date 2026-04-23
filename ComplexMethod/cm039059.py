def fit(self, X, y):
        """Fit the Linear Discriminant Analysis model.

        .. versionchanged:: 0.19
            `store_covariance` and `tol` has been moved to main constructor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        xp, _ = get_namespace(X)

        X, y = validate_data(
            self, X, y, ensure_min_samples=2, dtype=[xp.float64, xp.float32]
        )
        self.classes_ = unique_labels(y)
        n_samples, n_features = X.shape
        n_classes = self.classes_.shape[0]

        if n_samples == n_classes:
            raise ValueError(
                "The number of samples must be more than the number of classes."
            )

        if self.priors is None:  # estimate priors from sample
            _, cnts = xp.unique_counts(y)  # non-negative ints
            self.priors_ = xp.astype(cnts, X.dtype) / float(n_samples)
        else:
            self.priors_ = xp.asarray(self.priors, dtype=X.dtype)

        if xp.any(self.priors_ < 0):
            raise ValueError("priors must be non-negative")

        if xp.abs(xp.sum(self.priors_) - 1.0) > 1e-5:
            warnings.warn("The priors do not sum to 1. Renormalizing", UserWarning)
            self.priors_ = self.priors_ / self.priors_.sum()

        # Maximum number of components no matter what n_components is
        # specified:
        max_components = min(n_classes - 1, n_features)

        if self.n_components is None:
            self._max_components = max_components
        else:
            if self.n_components > max_components:
                raise ValueError(
                    "n_components cannot be larger than min(n_features, n_classes - 1)."
                )
            self._max_components = self.n_components

        if self.solver == "svd":
            if self.shrinkage is not None:
                raise NotImplementedError("shrinkage not supported with 'svd' solver.")
            if self.covariance_estimator is not None:
                raise ValueError(
                    "covariance estimator "
                    "is not supported "
                    "with svd solver. Try another solver"
                )
            self._solve_svd(X, y)
        elif self.solver == "lsqr":
            self._solve_lstsq(
                X,
                y,
                shrinkage=self.shrinkage,
                covariance_estimator=self.covariance_estimator,
            )
        elif self.solver == "eigen":
            self._solve_eigen(
                X,
                y,
                shrinkage=self.shrinkage,
                covariance_estimator=self.covariance_estimator,
            )
        if size(self.classes_) == 2:  # treat binary case as a special case
            coef_ = xp.asarray(self.coef_[1, :] - self.coef_[0, :], dtype=X.dtype)
            self.coef_ = xp.reshape(coef_, (1, -1))
            intercept_ = xp.asarray(
                self.intercept_[1] - self.intercept_[0], dtype=X.dtype
            )
            self.intercept_ = xp.reshape(intercept_, (1,))
        self._n_features_out = self._max_components
        return self