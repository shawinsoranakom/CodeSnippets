def fit(self, X, y, sample_weight=None):
        """Fit the SVM model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features) \
                or (n_samples, n_samples)
            Training vectors, where `n_samples` is the number of samples
            and `n_features` is the number of features.
            For kernel="precomputed", the expected shape of X is
            (n_samples, n_samples).

        y : array-like of shape (n_samples,)
            Target values (class labels in classification, real numbers in
            regression).

        sample_weight : array-like of shape (n_samples,), default=None
            Per-sample weights. Rescale C per sample. Higher weights
            force the classifier to put more emphasis on these points.

        Returns
        -------
        self : object
            Fitted estimator.

        Notes
        -----
        If X and y are not C-ordered and contiguous arrays of np.float64 and
        X is not a sparse CSR format, X and/or y may be copied.

        If X is a dense array, then the other methods will not support sparse
        matrices as input.
        """
        rnd = check_random_state(self.random_state)

        sparse = sp.issparse(X)
        if sparse and self.kernel == "precomputed":
            raise TypeError("Sparse precomputed kernels are not supported.")
        self._sparse = sparse and not callable(self.kernel)

        if callable(self.kernel):
            check_consistent_length(X, y)
        else:
            X, y = validate_data(
                self,
                X,
                y,
                dtype=np.float64,
                order="C",
                accept_sparse="csr",
                accept_large_sparse=False,
            )

        y = self._validate_targets(y)

        sample_weight = np.asarray(
            [] if sample_weight is None else sample_weight, dtype=np.float64
        )
        solver_type = LIBSVM_IMPL.index(self._impl)

        # TODO(1.11): remove probability
        self._effective_probability = self.probability
        if self._impl in ["c_svc", "nu_svc"]:
            if self._impl == "nu_scv":
                est_dep = "NuSVC"
            else:
                est_dep = "SVC"
            if self.probability != "deprecated":
                warnings.warn(
                    f"The `probability` parameter was deprecated in 1.9 and "
                    f"will be removed in version 1.11. "
                    f"Use `CalibratedClassifierCV({est_dep}(), ensemble=False)` "
                    f"instead of `{est_dep}(probability=True)`",
                    FutureWarning,
                )
            else:
                self._effective_probability = False

        # input validation
        n_samples = _num_samples(X)
        if solver_type != 2 and n_samples != y.shape[0]:
            raise ValueError(
                "X and y have incompatible shapes.\n"
                + "X has %s samples, but y has %s." % (n_samples, y.shape[0])
            )

        if self.kernel == "precomputed" and n_samples != X.shape[1]:
            raise ValueError(
                "Precomputed matrix must be a square matrix."
                " Input is a {}x{} matrix.".format(X.shape[0], X.shape[1])
            )

        if sample_weight.shape[0] > 0 and sample_weight.shape[0] != n_samples:
            raise ValueError(
                "sample_weight and X have incompatible shapes: "
                "%r vs %r\n"
                "Note: Sparse matrices cannot be indexed w/"
                "boolean masks (use `indices=True` in CV)."
                % (sample_weight.shape, X.shape)
            )

        kernel = "precomputed" if callable(self.kernel) else self.kernel

        if kernel == "precomputed":
            # unused but needs to be a float for cython code that ignores
            # it anyway
            self._gamma = 0.0
        elif isinstance(self.gamma, str):
            if self.gamma == "scale":
                # var = E[X^2] - E[X]^2 if sparse
                X_var = (X.multiply(X)).mean() - (X.mean()) ** 2 if sparse else X.var()
                self._gamma = 1.0 / (X.shape[1] * X_var) if X_var != 0 else 1.0
            elif self.gamma == "auto":
                self._gamma = 1.0 / X.shape[1]
        elif isinstance(self.gamma, Real):
            self._gamma = self.gamma

        fit = self._sparse_fit if self._sparse else self._dense_fit
        if self.verbose:
            print("[LibSVM]", end="")

        seed = rnd.randint(np.iinfo("i").max)
        fit(X, y, sample_weight, solver_type, kernel, random_seed=seed)
        # see comment on the other call to np.iinfo in this file

        self.shape_fit_ = X.shape if hasattr(X, "shape") else (n_samples,)

        # In binary case, we need to flip the sign of coef, intercept and
        # decision function. Use self._intercept_ and self._dual_coef_
        # internally.
        self._intercept_ = self.intercept_.copy()
        self._dual_coef_ = self.dual_coef_
        if self._impl in ["c_svc", "nu_svc"] and len(self.classes_) == 2:
            self.intercept_ *= -1
            self.dual_coef_ = -self.dual_coef_

        dual_coef = self._dual_coef_.data if self._sparse else self._dual_coef_
        intercept_finiteness = np.isfinite(self._intercept_).all()
        dual_coef_finiteness = np.isfinite(dual_coef).all()
        if not (intercept_finiteness and dual_coef_finiteness):
            raise ValueError(
                "The dual coefficients or intercepts are not finite."
                " The input data may contain large values and need to be"
                " preprocessed."
            )

        # Since, in the case of SVC and NuSVC, the number of models optimized by
        # libSVM could be greater than one (depending on the input), `n_iter_`
        # stores an ndarray.
        # For the other sub-classes (SVR, NuSVR, and OneClassSVM), the number of
        # models optimized by libSVM is always one, so `n_iter_` stores an
        # integer.
        if self._impl in ["c_svc", "nu_svc"]:
            self.n_iter_ = self._num_iter
        else:
            self.n_iter_ = self._num_iter.item()

        return self