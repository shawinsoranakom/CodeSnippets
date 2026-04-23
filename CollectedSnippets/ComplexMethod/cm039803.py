def fit(self, X, y):
        """Fit model to data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vectors, where `n_samples` is the number of samples and
            `n_features` is the number of predictors.

        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target vectors, where `n_samples` is the number of samples and
            `n_targets` is the number of response variables.

        Returns
        -------
        self : object
            Fitted model.
        """
        check_consistent_length(X, y)
        X = validate_data(
            self,
            X,
            dtype=np.float64,
            force_writeable=True,
            copy=self.copy,
            ensure_min_samples=2,
        )
        y = check_array(
            y,
            input_name="y",
            dtype=np.float64,
            force_writeable=True,
            copy=self.copy,
            ensure_2d=False,
        )
        if y.ndim == 1:
            self._predict_1d = True
            y = y.reshape(-1, 1)
        else:
            self._predict_1d = False

        n = X.shape[0]
        p = X.shape[1]
        q = y.shape[1]

        n_components = self.n_components
        # With PLSRegression n_components is bounded by the rank of (X.T X) see
        # Wegelin page 25. With CCA and PLSCanonical, n_components is bounded
        # by the rank of X and the rank of y: see Wegelin page 12
        rank_upper_bound = (
            min(n, p) if self.deflation_mode == "regression" else min(n, p, q)
        )
        if n_components > rank_upper_bound:
            raise ValueError(
                f"`n_components` upper bound is {rank_upper_bound}. "
                f"Got {n_components} instead. Reduce `n_components`."
            )

        self._norm_y_weights = self.deflation_mode == "canonical"  # 1.1
        norm_y_weights = self._norm_y_weights

        # Scale (in place)
        Xk, yk, self._x_mean, self._y_mean, self._x_std, self._y_std = _center_scale_xy(
            X, y, self.scale
        )

        self.x_weights_ = np.zeros((p, n_components))  # U
        self.y_weights_ = np.zeros((q, n_components))  # V
        self._x_scores = np.zeros((n, n_components))  # Xi
        self._y_scores = np.zeros((n, n_components))  # Omega
        self.x_loadings_ = np.zeros((p, n_components))  # Gamma
        self.y_loadings_ = np.zeros((q, n_components))  # Delta
        self.n_iter_ = []

        # This whole thing corresponds to the algorithm in section 4.1 of the
        # review from Wegelin. See above for a notation mapping from code to
        # paper.
        y_eps = np.finfo(yk.dtype).eps
        for k in range(n_components):
            # Find first left and right singular vectors of the X.T.dot(y)
            # cross-covariance matrix.
            if self.algorithm == "nipals":
                # Replace columns that are all close to zero with zeros
                yk_mask = np.all(np.abs(yk) < 10 * y_eps, axis=0)
                yk[:, yk_mask] = 0.0

                try:
                    (
                        x_weights,
                        y_weights,
                        n_iter_,
                    ) = _get_first_singular_vectors_power_method(
                        Xk,
                        yk,
                        mode=self.mode,
                        max_iter=self.max_iter,
                        tol=self.tol,
                        norm_y_weights=norm_y_weights,
                    )
                except StopIteration as e:
                    if str(e) != "y residual is constant":
                        raise
                    warnings.warn(f"y residual is constant at iteration {k}")
                    break

                self.n_iter_.append(n_iter_)

            elif self.algorithm == "svd":
                x_weights, y_weights = _get_first_singular_vectors_svd(Xk, yk)

            # inplace sign flip for consistency across solvers and archs
            _svd_flip_1d(x_weights, y_weights)

            # compute scores, i.e. the projections of X and y
            x_scores = np.dot(Xk, x_weights)
            if norm_y_weights:
                y_ss = 1
            else:
                y_ss = np.dot(y_weights, y_weights)
            y_scores = np.dot(yk, y_weights) / y_ss

            # Deflation: subtract rank-one approx to obtain Xk+1 and yk+1
            x_loadings = np.dot(x_scores, Xk) / np.dot(x_scores, x_scores)
            Xk -= np.outer(x_scores, x_loadings)

            if self.deflation_mode == "canonical":
                # regress yk on y_score
                y_loadings = np.dot(y_scores, yk) / np.dot(y_scores, y_scores)
                yk -= np.outer(y_scores, y_loadings)
            if self.deflation_mode == "regression":
                # regress yk on x_score
                y_loadings = np.dot(x_scores, yk) / np.dot(x_scores, x_scores)
                yk -= np.outer(x_scores, y_loadings)

            self.x_weights_[:, k] = x_weights
            self.y_weights_[:, k] = y_weights
            self._x_scores[:, k] = x_scores
            self._y_scores[:, k] = y_scores
            self.x_loadings_[:, k] = x_loadings
            self.y_loadings_[:, k] = y_loadings

        # X was approximated as Xi . Gamma.T + X_(R+1)
        # Xi . Gamma.T is a sum of n_components rank-1 matrices. X_(R+1) is
        # whatever is left to fully reconstruct X, and can be 0 if X is of rank
        # n_components.
        # Similarly, y was approximated as Omega . Delta.T + y_(R+1)

        # Compute transformation matrices (rotations_). See User Guide.
        self.x_rotations_ = np.dot(
            self.x_weights_,
            pinv(np.dot(self.x_loadings_.T, self.x_weights_), check_finite=False),
        )
        self.y_rotations_ = np.dot(
            self.y_weights_,
            pinv(np.dot(self.y_loadings_.T, self.y_weights_), check_finite=False),
        )
        self.coef_ = np.dot(self.x_rotations_, self.y_loadings_.T)
        self.coef_ = (self.coef_ * self._y_std).T / self._x_std
        self.intercept_ = self._y_mean
        self._n_features_out = self.x_rotations_.shape[1]
        return self