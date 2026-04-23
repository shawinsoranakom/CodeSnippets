def _fit_truncated(self, X, n_components, xp):
        """Fit the model by computing truncated SVD (by ARPACK or randomized)
        on X.
        """
        n_samples, n_features = X.shape

        svd_solver = self._fit_svd_solver
        if isinstance(n_components, str):
            raise ValueError(
                "n_components=%r cannot be a string with svd_solver='%s'"
                % (n_components, svd_solver)
            )
        elif not 1 <= n_components <= min(n_samples, n_features):
            raise ValueError(
                "n_components=%r must be between 1 and "
                "min(n_samples, n_features)=%r with "
                "svd_solver='%s'"
                % (n_components, min(n_samples, n_features), svd_solver)
            )
        elif svd_solver == "arpack" and n_components == min(n_samples, n_features):
            raise ValueError(
                "n_components=%r must be strictly less than "
                "min(n_samples, n_features)=%r with "
                "svd_solver='%s'"
                % (n_components, min(n_samples, n_features), svd_solver)
            )

        random_state = check_random_state(self.random_state)

        # Center data
        total_var = None
        if issparse(X):
            self.mean_, var = mean_variance_axis(X, axis=0)
            total_var = var.sum() * n_samples / (n_samples - 1)  # ddof=1
            X_centered = _implicit_column_offset(X, self.mean_)
            x_is_centered = False
        else:
            self.mean_ = xp.mean(X, axis=0)
            X_centered = xp.asarray(X, copy=True) if self.copy else X
            X_centered -= self.mean_
            x_is_centered = not self.copy

        if svd_solver == "arpack":
            v0 = _init_arpack_v0(min(X.shape), random_state)
            U, S, Vt = svds(X_centered, k=n_components, tol=self.tol, v0=v0)
            # svds doesn't abide by scipy.linalg.svd/randomized_svd
            # conventions, so reverse its outputs.
            S = S[::-1]
            # flip eigenvectors' sign to enforce deterministic output
            U, Vt = svd_flip(U[:, ::-1], Vt[::-1], u_based_decision=False)

        elif svd_solver == "randomized":
            # sign flipping is done inside
            U, S, Vt = _randomized_svd(
                X_centered,
                n_components=n_components,
                n_oversamples=self.n_oversamples,
                n_iter=self.iterated_power,
                power_iteration_normalizer=self.power_iteration_normalizer,
                flip_sign=False,
                random_state=random_state,
            )
            U, Vt = svd_flip(U, Vt, u_based_decision=False)

        self.n_samples_ = n_samples
        self.components_ = Vt
        self.n_components_ = n_components

        # Get variance explained by singular values
        self.explained_variance_ = (S**2) / (n_samples - 1)

        # Workaround in-place variance calculation since at the time numpy
        # did not have a way to calculate variance in-place.
        #
        # TODO: update this code to either:
        # * Use the array-api variance calculation, unless memory usage suffers
        # * Update sklearn.utils.extmath._incremental_mean_and_var to support array-api
        # See: https://github.com/scikit-learn/scikit-learn/pull/18689#discussion_r1335540991
        if total_var is None:
            N = X.shape[0] - 1
            X_centered **= 2
            total_var = xp.sum(X_centered) / N

        self.explained_variance_ratio_ = self.explained_variance_ / total_var
        self.singular_values_ = xp.asarray(S, copy=True)  # Store the singular values.

        if self.n_components_ < min(n_features, n_samples):
            self.noise_variance_ = total_var - xp.sum(self.explained_variance_)
            self.noise_variance_ /= min(n_features, n_samples) - n_components
        else:
            self.noise_variance_ = 0.0

        return U, S, Vt, X, x_is_centered, xp