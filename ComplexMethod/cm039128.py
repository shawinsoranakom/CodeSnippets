def _fit_full(self, X, n_components, xp, is_array_api_compliant):
        """Fit the model by computing full SVD on X."""
        n_samples, n_features = X.shape

        if n_components == "mle":
            if n_samples < n_features:
                raise ValueError(
                    "n_components='mle' is only supported if n_samples >= n_features"
                )
        elif not 0 <= n_components <= min(n_samples, n_features):
            raise ValueError(
                f"n_components={n_components} must be between 0 and "
                f"min(n_samples, n_features)={min(n_samples, n_features)} with "
                f"svd_solver={self._fit_svd_solver!r}"
            )

        self.mean_ = xp.mean(X, axis=0)
        # When X is a scipy sparse matrix, self.mean_ is a numpy matrix, so we need
        # to transform it to a 1D array. Note that this is not the case when X
        # is a scipy sparse array.
        # TODO: remove the following two lines when scikit-learn only depends
        # on scipy versions that no longer support scipy.sparse matrices.
        self.mean_ = xp.reshape(xp.asarray(self.mean_), (-1,))

        if self._fit_svd_solver == "full":
            X_centered = xp.asarray(X, copy=True) if self.copy else X
            X_centered -= self.mean_
            x_is_centered = not self.copy

            if not is_array_api_compliant:
                # Use scipy.linalg with NumPy/SciPy inputs for the sake of not
                # introducing unanticipated behavior changes. In the long run we
                # could instead decide to always use xp.linalg.svd for all inputs,
                # but that would make this code rely on numpy's SVD instead of
                # scipy's. It's not 100% clear whether they use the same LAPACK
                # solver by default though (assuming both are built against the
                # same BLAS).
                U, S, Vt = linalg.svd(X_centered, full_matrices=False)
            else:
                U, S, Vt = xp.linalg.svd(X_centered, full_matrices=False)
            explained_variance_ = (S**2) / (n_samples - 1)

        else:
            assert self._fit_svd_solver == "covariance_eigh"
            # In the following, we center the covariance matrix C afterwards
            # (without centering the data X first) to avoid an unnecessary copy
            # of X. Note that the mean_ attribute is still needed to center
            # test data in the transform method.
            #
            # Note: at the time of writing, `xp.cov` does not exist in the
            # Array API standard:
            # https://github.com/data-apis/array-api/issues/43
            #
            # Besides, using `numpy.cov`, as of numpy 1.26.0, would not be
            # memory efficient for our use case when `n_samples >> n_features`:
            # `numpy.cov` centers a copy of the data before computing the
            # matrix product instead of subtracting a small `(n_features,
            # n_features)` square matrix from the gram matrix X.T @ X, as we do
            # below.
            x_is_centered = False
            C = X.T @ X
            C -= (
                n_samples
                * xp.reshape(self.mean_, (-1, 1))
                * xp.reshape(self.mean_, (1, -1))
            )
            C /= n_samples - 1
            eigenvals, eigenvecs = xp.linalg.eigh(C)

            # When X is a scipy sparse matrix, the following two datastructures
            # are returned as instances of the soft-deprecated numpy.matrix
            # class. Note that this problem does not occur when X is a scipy
            # sparse array (or another other kind of supported array).
            # TODO: remove the following two lines when scikit-learn only
            # depends on scipy versions that no longer support scipy.sparse
            # matrices.
            eigenvals = xp.reshape(xp.asarray(eigenvals), (-1,))
            eigenvecs = xp.asarray(eigenvecs)

            eigenvals = xp.flip(eigenvals, axis=0)
            eigenvecs = xp.flip(eigenvecs, axis=1)

            # The covariance matrix C is positive semi-definite by
            # construction. However, the eigenvalues returned by xp.linalg.eigh
            # can be slightly negative due to numerical errors. This would be
            # an issue for the subsequent sqrt, hence the manual clipping.
            eigenvals[eigenvals < 0.0] = 0.0
            explained_variance_ = eigenvals

            # Re-construct SVD of centered X indirectly and make it consistent
            # with the other solvers.
            S = xp.sqrt(eigenvals * (n_samples - 1))
            Vt = eigenvecs.T
            U = None

        # flip eigenvectors' sign to enforce deterministic output
        U, Vt = svd_flip(U, Vt, u_based_decision=False)

        components_ = Vt

        # Get variance explained by singular values
        total_var = xp.sum(explained_variance_)
        explained_variance_ratio_ = explained_variance_ / total_var
        singular_values_ = xp.asarray(S, copy=True)  # Store the singular values.

        # Postprocess the number of components required
        if n_components == "mle":
            n_components = _infer_dimension(explained_variance_, n_samples)
        elif 0 < n_components < 1.0:
            # number of components for which the cumulated explained
            # variance percentage is superior to the desired threshold
            # side='right' ensures that number of features selected
            # their variance is always greater than n_components float
            # passed. More discussion in issue: #15669
            ratio_cumsum = xp.cumulative_sum(explained_variance_ratio_)
            n_components = (
                xp.searchsorted(
                    ratio_cumsum,
                    xp.asarray(n_components, device=device(ratio_cumsum)),
                    side="right",
                )
                + 1
            )

        # Compute noise covariance using Probabilistic PCA model
        # The sigma2 maximum likelihood (cf. eq. 12.46)
        if n_components < min(n_features, n_samples):
            self.noise_variance_ = xp.mean(explained_variance_[n_components:])
        else:
            self.noise_variance_ = 0.0

        self.n_samples_ = n_samples
        self.n_components_ = n_components
        # Assign a copy of the result of the truncation of the components in
        # order to:
        # - release the memory used by the discarded components,
        # - ensure that the kept components are allocated contiguously in
        #   memory to make the transform method faster by leveraging cache
        #   locality.
        self.components_ = xp.asarray(components_[:n_components, :], copy=True)

        # We do the same for the other arrays for the sake of consistency.
        self.explained_variance_ = xp.asarray(
            explained_variance_[:n_components], copy=True
        )
        self.explained_variance_ratio_ = xp.asarray(
            explained_variance_ratio_[:n_components], copy=True
        )
        self.singular_values_ = xp.asarray(singular_values_[:n_components], copy=True)

        return U, S, Vt, X, x_is_centered, xp