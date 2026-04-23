def _fit_transform(self, X, y=None, W=None, H=None, update_H=True):
        X = check_array(X, accept_sparse=("csr", "csc"))
        check_non_negative(X, "NMF (input X)")

        n_samples, n_features = X.shape
        n_components = self.n_components
        if n_components is None:
            n_components = n_features

        if not isinstance(n_components, numbers.Integral) or n_components <= 0:
            raise ValueError(
                "Number of components must be a positive integer; got (n_components=%r)"
                % n_components
            )
        if not isinstance(self.max_iter, numbers.Integral) or self.max_iter < 0:
            raise ValueError(
                "Maximum number of iterations must be a positive "
                "integer; got (max_iter=%r)" % self.max_iter
            )
        if not isinstance(self.tol, numbers.Number) or self.tol < 0:
            raise ValueError(
                "Tolerance for stopping criteria must be positive; got (tol=%r)"
                % self.tol
            )

        # check W and H, or initialize them
        if self.init == "custom" and update_H:
            _check_init(H, (n_components, n_features), "NMF (input H)")
            _check_init(W, (n_samples, n_components), "NMF (input W)")
        elif not update_H:
            _check_init(H, (n_components, n_features), "NMF (input H)")
            W = np.zeros((n_samples, n_components))
        else:
            W, H = _initialize_nmf(
                X, n_components, init=self.init, random_state=self.random_state
            )

        if update_H:  # fit_transform
            W, H, n_iter = _fit_projected_gradient(
                X,
                W,
                H,
                self.tol,
                self.max_iter,
                self.nls_max_iter,
                self.alpha,
                self.l1_ratio,
            )
        else:  # transform
            Wt, _, n_iter = _nls_subproblem(
                X.T,
                H.T,
                W.T,
                self.tol,
                self.nls_max_iter,
                alpha=self.alpha,
                l1_ratio=self.l1_ratio,
            )
            W = Wt.T

        if n_iter == self.max_iter and self.tol > 0:
            warnings.warn(
                "Maximum number of iteration %d reached. Increase it"
                " to improve convergence." % self.max_iter,
                ConvergenceWarning,
            )

        return W, H, n_iter