def _fit(self, X, y=None, force_transform=False):
        X = self._check_input(X, in_fit=True, check_positive=True)

        if not self.copy and not force_transform:  # if call from fit()
            X = X.copy()  # force copy so that fit does not change X inplace

        n_samples = X.shape[0]
        mean = np.mean(X, axis=0, dtype=np.float64)
        var = np.var(X, axis=0, dtype=np.float64)

        optim_function = {
            "box-cox": self._box_cox_optimize,
            "yeo-johnson": self._yeo_johnson_optimize,
        }[self.method]

        transform_function = {
            "box-cox": boxcox,
            "yeo-johnson": stats.yeojohnson,
        }[self.method]

        with np.errstate(invalid="ignore"):  # hide NaN warnings
            self.lambdas_ = np.empty(X.shape[1], dtype=X.dtype)
            for i, col in enumerate(X.T):
                # For yeo-johnson, leave constant features unchanged
                # lambda=1 corresponds to the identity transformation
                is_constant_feature = _is_constant_feature(var[i], mean[i], n_samples)
                if self.method == "yeo-johnson" and is_constant_feature:
                    self.lambdas_[i] = 1.0
                    continue

                self.lambdas_[i] = optim_function(col)

                if self.standardize or force_transform:
                    X[:, i] = transform_function(X[:, i], self.lambdas_[i])

        if self.standardize:
            self._scaler = StandardScaler(copy=False).set_output(transform="default")
            if force_transform:
                X = self._scaler.fit_transform(X)
            else:
                self._scaler.fit(X)

        return X