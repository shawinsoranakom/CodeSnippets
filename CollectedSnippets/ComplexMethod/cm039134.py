def fit(self, X, y=None):
        """Fit the FactorAnalysis model to X using SVD based approach.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : Ignored
            Ignored parameter.

        Returns
        -------
        self : object
            FactorAnalysis class instance.
        """
        X = validate_data(
            self, X, copy=self.copy, dtype=np.float64, force_writeable=True
        )

        n_samples, n_features = X.shape
        n_components = self.n_components
        if n_components is None:
            n_components = n_features

        self.mean_ = np.mean(X, axis=0)
        X -= self.mean_

        # some constant terms
        nsqrt = sqrt(n_samples)
        llconst = n_features * log(2.0 * np.pi) + n_components
        var = np.var(X, axis=0)

        if self.noise_variance_init is None:
            psi = np.ones(n_features, dtype=X.dtype)
        else:
            if len(self.noise_variance_init) != n_features:
                raise ValueError(
                    "noise_variance_init dimension does not "
                    "with number of features : %d != %d"
                    % (len(self.noise_variance_init), n_features)
                )
            psi = np.array(self.noise_variance_init)

        loglike = []
        old_ll = -np.inf
        SMALL = 1e-12

        # we'll modify svd outputs to return unexplained variance
        # to allow for unified computation of loglikelihood
        if self.svd_method == "lapack":

            def my_svd(X):
                _, s, Vt = linalg.svd(X, full_matrices=False, check_finite=False)
                return (
                    s[:n_components],
                    Vt[:n_components],
                    squared_norm(s[n_components:]),
                )

        else:  # svd_method == "randomized"
            random_state = check_random_state(self.random_state)

            def my_svd(X):
                _, s, Vt = _randomized_svd(
                    X,
                    n_components,
                    random_state=random_state,
                    n_iter=self.iterated_power,
                )
                return s, Vt, squared_norm(X) - squared_norm(s)

        for i in range(self.max_iter):
            # SMALL helps numerics
            sqrt_psi = np.sqrt(psi) + SMALL
            s, Vt, unexp_var = my_svd(X / (sqrt_psi * nsqrt))
            s **= 2
            # Use 'maximum' here to avoid sqrt problems.
            W = np.sqrt(np.maximum(s - 1.0, 0.0))[:, np.newaxis] * Vt
            del Vt
            W *= sqrt_psi

            # loglikelihood
            ll = llconst + np.sum(np.log(s))
            ll += unexp_var + np.sum(np.log(psi))
            ll *= -n_samples / 2.0
            loglike.append(ll)
            if (ll - old_ll) < self.tol:
                break
            old_ll = ll

            psi = np.maximum(var - np.sum(W**2, axis=0), SMALL)
        else:
            warnings.warn(
                "FactorAnalysis did not converge."
                " You might want"
                " to increase the number of iterations.",
                ConvergenceWarning,
            )

        self.components_ = W
        if self.rotation is not None:
            self.components_ = self._rotate(W)
        self.noise_variance_ = psi
        self.loglike_ = loglike
        self.n_iter_ = i + 1
        return self