def _fit(self, X):
        """Dispatch to the right submethod depending on the chosen solver."""
        xp, is_array_api_compliant = get_namespace(X)

        # Raise an error for sparse input and unsupported svd_solver
        if issparse(X) and self.svd_solver not in ["auto", "arpack", "covariance_eigh"]:
            raise TypeError(
                'PCA only support sparse inputs with the "arpack" and'
                f' "covariance_eigh" solvers, while "{self.svd_solver}" was passed. See'
                " TruncatedSVD for a possible alternative."
            )
        if self.svd_solver == "arpack" and is_array_api_compliant:
            raise ValueError(
                "PCA with svd_solver='arpack' is not supported for Array API inputs."
            )

        # Validate the data, without ever forcing a copy as any solver that
        # supports sparse input data and the `covariance_eigh` solver are
        # written in a way to avoid the need for any inplace modification of
        # the input data contrary to the other solvers.
        # The copy will happen
        # later, only if needed, once the solver negotiation below is done.
        X = validate_data(
            self,
            X,
            dtype=[xp.float64, xp.float32],
            force_writeable=True,
            accept_sparse=("csr", "csc"),
            ensure_2d=True,
            copy=False,
        )
        self._fit_svd_solver = self.svd_solver
        if self._fit_svd_solver == "auto" and issparse(X):
            self._fit_svd_solver = "arpack"

        if self.n_components is None:
            if self._fit_svd_solver != "arpack":
                n_components = min(X.shape)
            else:
                n_components = min(X.shape) - 1
        else:
            n_components = self.n_components

        if self._fit_svd_solver == "auto":
            # Tall and skinny problems are best handled by precomputing the
            # covariance matrix.
            if X.shape[1] <= 1_000 and X.shape[0] >= 10 * X.shape[1]:
                self._fit_svd_solver = "covariance_eigh"
            # Small problem or n_components == 'mle', just call full PCA
            elif max(X.shape) <= 500 or n_components == "mle":
                self._fit_svd_solver = "full"
            elif 1 <= n_components < 0.8 * min(X.shape):
                self._fit_svd_solver = "randomized"
            # This is also the case of n_components in (0, 1)
            else:
                self._fit_svd_solver = "full"

        # Call different fits for either full or truncated SVD
        if self._fit_svd_solver in ("full", "covariance_eigh"):
            return self._fit_full(X, n_components, xp, is_array_api_compliant)
        elif self._fit_svd_solver in ["arpack", "randomized"]:
            return self._fit_truncated(X, n_components, xp)