def fit(self, X, y, sample_weight=None):
        """Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values. Will be cast to X's dtype if necessary.

        sample_weight : ndarray of shape (n_samples,), default=None
            Individual weights for each sample.

            .. versionadded:: 0.20
               parameter *sample_weight* support to BayesianRidge.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        X, y = validate_data(
            self,
            X,
            y,
            dtype=[np.float64, np.float32],
            force_writeable=True,
            y_numeric=True,
        )
        dtype = X.dtype
        n_samples, n_features = X.shape

        sw_sum = n_samples
        y_var = y.var()
        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=dtype)
            sw_sum = sample_weight.sum()
            y_mean = np.average(y, weights=sample_weight)
            y_var = np.average((y - y_mean) ** 2, weights=sample_weight)

        X, y, X_offset_, y_offset_, X_scale_, _ = _preprocess_data(
            X,
            y,
            fit_intercept=self.fit_intercept,
            copy=self.copy_X,
            sample_weight=sample_weight,
            # Sample weight can be implemented via a simple rescaling.
            rescale_with_sw=True,
        )

        self.X_offset_ = X_offset_
        self.X_scale_ = X_scale_

        # Initialization of the values of the parameters
        eps = np.finfo(np.float64).eps
        # Add `eps` in the denominator to omit division by zero
        alpha_ = self.alpha_init
        lambda_ = self.lambda_init
        if alpha_ is None:
            alpha_ = 1.0 / (y_var + eps)
        if lambda_ is None:
            lambda_ = 1.0

        # Avoid unintended type promotion to float64 with numpy 2
        alpha_ = np.asarray(alpha_, dtype=dtype)
        lambda_ = np.asarray(lambda_, dtype=dtype)

        verbose = self.verbose
        lambda_1 = self.lambda_1
        lambda_2 = self.lambda_2
        alpha_1 = self.alpha_1
        alpha_2 = self.alpha_2

        self.scores_ = list()
        coef_old_ = None

        XT_y = np.dot(X.T, y)
        # Let M, N = n_samples, n_features and K = min(M, N).
        # The posterior covariance matrix needs Vh_full: (N, N).
        # The full SVD is only required when n_samples < n_features.
        # When n_samples < n_features, K=M and full_matrices=True
        # U: (M, M), S: M, Vh_full: (N, N), Vh: (M, N)
        # When n_samples > n_features, K=N and full_matrices=False
        # U: (M, N), S: N, Vh_full: (N, N), Vh: (N, N)
        U, S, Vh_full = linalg.svd(X, full_matrices=(n_samples < n_features))
        K = len(S)
        eigen_vals_ = S**2
        eigen_vals_full = np.zeros(n_features, dtype=dtype)
        eigen_vals_full[0:K] = eigen_vals_
        Vh = Vh_full[0:K, :]

        # Convergence loop of the bayesian ridge regression
        for iter_ in range(self.max_iter):
            # update posterior mean coef_ based on alpha_ and lambda_ and
            # compute corresponding sse (sum of squared errors)
            coef_, sse_ = self._update_coef_(
                X, y, n_samples, n_features, XT_y, U, Vh, eigen_vals_, alpha_, lambda_
            )
            if self.compute_score:
                # compute the log marginal likelihood
                s = self._log_marginal_likelihood(
                    n_samples,
                    n_features,
                    sw_sum,
                    eigen_vals_,
                    alpha_,
                    lambda_,
                    coef_,
                    sse_,
                )
                self.scores_.append(s)

            # Update alpha and lambda according to (MacKay, 1992)
            gamma_ = np.sum((alpha_ * eigen_vals_) / (lambda_ + alpha_ * eigen_vals_))
            lambda_ = (gamma_ + 2 * lambda_1) / (np.sum(coef_**2) + 2 * lambda_2)
            alpha_ = (sw_sum - gamma_ + 2 * alpha_1) / (sse_ + 2 * alpha_2)

            # Check for convergence
            if iter_ != 0 and np.sum(np.abs(coef_old_ - coef_)) < self.tol:
                if verbose:
                    print("Convergence after ", str(iter_), " iterations")
                break
            coef_old_ = np.copy(coef_)

        self.n_iter_ = iter_ + 1

        # return regularization parameters and corresponding posterior mean,
        # log marginal likelihood and posterior covariance
        self.alpha_ = alpha_
        self.lambda_ = lambda_
        self.coef_, sse_ = self._update_coef_(
            X, y, n_samples, n_features, XT_y, U, Vh, eigen_vals_, alpha_, lambda_
        )
        if self.compute_score:
            # compute the log marginal likelihood
            s = self._log_marginal_likelihood(
                n_samples,
                n_features,
                sw_sum,
                eigen_vals_,
                alpha_,
                lambda_,
                coef_,
                sse_,
            )
            self.scores_.append(s)
            self.scores_ = np.array(self.scores_)

        # posterior covariance
        self.sigma_ = np.dot(
            Vh_full.T, Vh_full / (alpha_ * eigen_vals_full + lambda_)[:, np.newaxis]
        )

        self._set_intercept(X_offset_, y_offset_, X_scale_)

        return self