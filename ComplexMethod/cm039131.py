def _fit_transform(self, X, compute_sources=False):
        """Fit the model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data, where `n_samples` is the number of samples
            and `n_features` is the number of features.

        compute_sources : bool, default=False
            If False, sources are not computes but only the rotation matrix.
            This can save memory when working with big data. Defaults to False.

        Returns
        -------
        S : ndarray of shape (n_samples, n_components) or None
            Sources matrix. `None` if `compute_sources` is `False`.
        """
        XT = validate_data(
            self,
            X,
            copy=self.whiten,
            dtype=[np.float64, np.float32],
            ensure_min_samples=2,
        ).T
        fun_args = {} if self.fun_args is None else self.fun_args
        random_state = check_random_state(self.random_state)

        alpha = fun_args.get("alpha", 1.0)
        if not 1 <= alpha <= 2:
            raise ValueError("alpha must be in [1,2]")

        if self.fun == "logcosh":
            g = _logcosh
        elif self.fun == "exp":
            g = _exp
        elif self.fun == "cube":
            g = _cube
        elif callable(self.fun):

            def g(x, fun_args):
                return self.fun(x, **fun_args)

        n_features, n_samples = XT.shape
        n_components = self.n_components
        if not self.whiten and n_components is not None:
            n_components = None
            warnings.warn("Ignoring n_components with whiten=False.")

        if n_components is None:
            n_components = min(n_samples, n_features)
        if n_components > min(n_samples, n_features):
            n_components = min(n_samples, n_features)
            warnings.warn(
                "n_components is too large: it will be set to %s" % n_components
            )

        if self.whiten:
            # Centering the features of X
            X_mean = XT.mean(axis=-1)
            XT -= X_mean[:, np.newaxis]

            # Whitening and preprocessing by PCA
            if self.whiten_solver == "eigh":
                # Faster when num_samples >> n_features
                d, u = linalg.eigh(XT.dot(X))
                sort_indices = np.argsort(d)[::-1]
                eps = np.finfo(d.dtype).eps * 10
                degenerate_idx = d < eps
                if np.any(degenerate_idx):
                    warnings.warn(
                        "There are some small singular values, using "
                        "whiten_solver = 'svd' might lead to more "
                        "accurate results."
                    )
                d[degenerate_idx] = eps  # For numerical issues
                np.sqrt(d, out=d)
                d, u = d[sort_indices], u[:, sort_indices]
            elif self.whiten_solver == "svd":
                u, d = linalg.svd(XT, full_matrices=False, check_finite=False)[:2]

            # Give consistent eigenvectors for both svd solvers
            u *= np.sign(u[0])

            K = (u / d).T[:n_components]  # see (6.33) p.140
            del u, d
            X1 = np.dot(K, XT)
            # see (13.6) p.267 Here X1 is white and data
            # in X has been projected onto a subspace by PCA
            X1 *= np.sqrt(n_samples)
        else:
            # X must be casted to floats to avoid typing issues with numpy
            # 2.0 and the line below
            X1 = as_float_array(XT, copy=False)  # copy has been taken care of

        w_init = self.w_init
        if w_init is None:
            w_init = np.asarray(
                random_state.normal(size=(n_components, n_components)), dtype=X1.dtype
            )

        else:
            w_init = np.asarray(w_init)
            if w_init.shape != (n_components, n_components):
                raise ValueError(
                    "w_init has invalid shape -- should be %(shape)s"
                    % {"shape": (n_components, n_components)}
                )

        kwargs = {
            "tol": self.tol,
            "g": g,
            "fun_args": fun_args,
            "max_iter": self.max_iter,
            "w_init": w_init,
        }

        if self.algorithm == "parallel":
            W, n_iter = _ica_par(X1, **kwargs)
        elif self.algorithm == "deflation":
            W, n_iter = _ica_def(X1, **kwargs)
        del X1

        self.n_iter_ = n_iter

        if compute_sources:
            if self.whiten:
                S = np.linalg.multi_dot([W, K, XT]).T
            else:
                S = np.dot(W, XT).T
        else:
            S = None

        if self.whiten:
            if self.whiten == "unit-variance":
                if not compute_sources:
                    S = np.linalg.multi_dot([W, K, XT]).T
                S_std = np.std(S, axis=0, keepdims=True)
                S /= S_std
                W /= S_std.T

            self.components_ = np.dot(W, K)
            self.mean_ = X_mean
            self.whitening_ = K
        else:
            self.components_ = W

        self.mixing_ = linalg.pinv(self.components_, check_finite=False)
        self._unmixing = W

        return S