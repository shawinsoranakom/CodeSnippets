def fit_transform(self, X, y=None):
        """Fit model to X and perform dimensionality reduction on X.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Reduced version of X. This will always be a dense array.
        """
        X = validate_data(self, X, accept_sparse=["csr", "csc"], ensure_min_features=2)
        random_state = check_random_state(self.random_state)

        if self.algorithm == "arpack":
            v0 = _init_arpack_v0(min(X.shape), random_state)
            U, Sigma, VT = svds(X, k=self.n_components, tol=self.tol, v0=v0)
            # svds doesn't abide by scipy.linalg.svd/randomized_svd
            # conventions, so reverse its outputs.
            Sigma = Sigma[::-1]
            # u_based_decision=False is needed to be consistent with PCA.
            U, VT = svd_flip(U[:, ::-1], VT[::-1], u_based_decision=False)

        elif self.algorithm == "randomized":
            if self.n_components > X.shape[1]:
                raise ValueError(
                    f"n_components({self.n_components}) must be <="
                    f" n_features({X.shape[1]})."
                )
            U, Sigma, VT = _randomized_svd(
                X,
                self.n_components,
                n_iter=self.n_iter,
                n_oversamples=self.n_oversamples,
                power_iteration_normalizer=self.power_iteration_normalizer,
                random_state=random_state,
                flip_sign=False,
            )
            U, VT = svd_flip(U, VT, u_based_decision=False)

        self.components_ = VT

        # As a result of the SVD approximation error on X ~ U @ Sigma @ V.T,
        # X @ V is not the same as U @ Sigma
        if self.algorithm == "randomized" or (
            self.algorithm == "arpack" and self.tol > 0
        ):
            X_transformed = safe_sparse_dot(X, self.components_.T)
        else:
            X_transformed = U * Sigma

        # Calculate explained variance & explained variance ratio
        self.explained_variance_ = exp_var = np.var(X_transformed, axis=0)
        if sp.issparse(X):
            _, full_var = mean_variance_axis(X, axis=0)
            full_var = full_var.sum()
        else:
            full_var = np.var(X, axis=0).sum()
        self.explained_variance_ratio_ = exp_var / full_var
        self.singular_values_ = Sigma  # Store the singular values.

        return X_transformed