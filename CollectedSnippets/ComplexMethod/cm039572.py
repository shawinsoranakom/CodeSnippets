def _fit(self, X, y, max_iter, alpha, fit_path, Xy=None):
        """Auxiliary method to fit the model using X, y as training data"""
        n_features = X.shape[1]

        X, y, X_offset, y_offset, X_scale, _ = _preprocess_data(
            X, y, fit_intercept=self.fit_intercept, copy=self.copy_X
        )

        if y.ndim == 1:
            y = y[:, np.newaxis]

        n_targets = y.shape[1]

        Gram = self._get_gram(self.precompute, X, y)

        self.alphas_ = []
        self.n_iter_ = []
        self.coef_ = np.empty((n_targets, n_features), dtype=X.dtype)

        if fit_path:
            self.active_ = []
            self.coef_path_ = []
            for k in range(n_targets):
                this_Xy = None if Xy is None else Xy[:, k]
                alphas, active, coef_path, n_iter_ = lars_path(
                    X,
                    y[:, k],
                    Gram=Gram,
                    Xy=this_Xy,
                    copy_X=self.copy_X,
                    copy_Gram=True,
                    alpha_min=alpha,
                    method=self.method,
                    verbose=max(0, self.verbose - 1),
                    max_iter=max_iter,
                    eps=self.eps,
                    return_path=True,
                    return_n_iter=True,
                    positive=self.positive,
                )
                self.alphas_.append(alphas)
                self.active_.append(active)
                self.n_iter_.append(n_iter_)
                self.coef_path_.append(coef_path)
                self.coef_[k] = coef_path[:, -1]

            if n_targets == 1:
                self.alphas_, self.active_, self.coef_path_, self.coef_ = [
                    a[0]
                    for a in (self.alphas_, self.active_, self.coef_path_, self.coef_)
                ]
                self.n_iter_ = self.n_iter_[0]
        else:
            for k in range(n_targets):
                this_Xy = None if Xy is None else Xy[:, k]
                alphas, _, self.coef_[k], n_iter_ = lars_path(
                    X,
                    y[:, k],
                    Gram=Gram,
                    Xy=this_Xy,
                    copy_X=self.copy_X,
                    copy_Gram=True,
                    alpha_min=alpha,
                    method=self.method,
                    verbose=max(0, self.verbose - 1),
                    max_iter=max_iter,
                    eps=self.eps,
                    return_path=False,
                    return_n_iter=True,
                    positive=self.positive,
                )
                self.alphas_.append(alphas)
                self.n_iter_.append(n_iter_)
            if n_targets == 1:
                self.alphas_ = self.alphas_[0]
                self.n_iter_ = self.n_iter_[0]

        self._set_intercept(X_offset, y_offset, X_scale)
        return self