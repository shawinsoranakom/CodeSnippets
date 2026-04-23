def fit(self, X, y, sample_weight=None):
        """
        Fit the model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target vector relative to X.

        sample_weight : array-like of shape (n_samples,) default=None
            Array of weights that are assigned to individual samples.
            If not provided, then each sample is given unit weight.

            .. versionadded:: 0.17
               *sample_weight* support to LogisticRegression.

        Returns
        -------
        self
            Fitted estimator.

        Notes
        -----
        The SAGA solver supports both float64 and float32 bit arrays.
        """
        if self.penalty == "deprecated":
            if self.l1_ratio == 0 or self.l1_ratio is None:
                penalty = "l2"
                if self.l1_ratio is None:
                    warnings.warn(
                        (
                            "'l1_ratio=None' was deprecated in version 1.8 and will "
                            "trigger an error in 1.10. Use 0<=l1_ratio<=1 instead."
                        ),
                        FutureWarning,
                    )
            elif self.l1_ratio == 1:
                penalty = "l1"
            else:
                penalty = "elasticnet"
            if self.C == np.inf:
                penalty = None
        else:
            penalty = self.penalty
            warnings.warn(
                (
                    "'penalty' was deprecated in version 1.8 and will be removed in"
                    " 1.10. To avoid this warning, leave 'penalty' set to its default"
                    " value and use 'l1_ratio' or 'C' instead."
                    " Use l1_ratio=0 instead of penalty='l2',"
                    " l1_ratio=1 instead of penalty='l1', and "
                    "C=np.inf instead of penalty=None."
                ),
                FutureWarning,
            )

        solver = _check_solver(self.solver, penalty, self.dual)

        if penalty != "elasticnet" and (
            self.l1_ratio is not None and 0 < self.l1_ratio < 1
        ):
            warnings.warn(
                "l1_ratio parameter is only used when penalty is "
                "'elasticnet'. Got "
                "(penalty={})".format(penalty)
            )
        if (self.penalty == "l2" and self.l1_ratio != 0) or (
            self.penalty == "l1" and self.l1_ratio != 1
        ):
            warnings.warn(
                f"Inconsistent values: penalty={self.penalty} with "
                f"l1_ratio={self.l1_ratio}. penalty is deprecated. Please use "
                f"l1_ratio only."
            )
        if penalty == "elasticnet" and self.l1_ratio is None:
            raise ValueError("l1_ratio must be specified when penalty is elasticnet.")

        xp, _, device_ = get_namespace_and_device(X)
        xp_y, _ = get_namespace(y)

        if self.penalty is None:
            if self.C != 1.0:  # default value
                warnings.warn(
                    "Setting penalty=None will ignore the C and l1_ratio parameters"
                )
                # Note that check for l1_ratio is done right above
            C_ = xp.inf
            penalty = "l2"
        else:
            C_ = self.C

        msg = (
            "'n_jobs' has no effect since 1.8 and will be removed in 1.10. "
            f"You provided 'n_jobs={self.n_jobs}', please leave it unspecified."
        )
        if self.n_jobs is not None:
            warnings.warn(msg, category=FutureWarning)

        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse="csr",
            dtype=[xp.float64, xp.float32],
            order="C",
            accept_large_sparse=solver not in ["liblinear", "sag", "saga"],
        )
        n_features = X.shape[1]
        check_classification_targets(y)
        self.classes_ = xp_y.unique_values(y)
        n_classes = size(self.classes_)
        is_binary = n_classes == 2

        if solver == "liblinear":
            if not is_binary:
                raise ValueError(
                    "The 'liblinear' solver does not support multiclass classification"
                    " (n_classes >= 3). Either use another solver or wrap the "
                    "estimator in a OneVsRestClassifier to keep applying a "
                    "one-versus-rest scheme."
                )
            if np.max(X) > 1e30:
                raise ValueError(
                    "Using the 'liblinear' solver while X contains a maximum "
                    "value > 1e30 results in a frozen fit. Please choose another "
                    "solver or rescale the input X."
                )
            self.coef_, self.intercept_, self.n_iter_ = _fit_liblinear(
                X,
                y,
                self.C,
                self.fit_intercept,
                self.intercept_scaling,
                self.class_weight,
                penalty,
                self.dual,
                self.verbose,
                self.max_iter,
                self.tol,
                self.random_state,
                sample_weight=sample_weight,
            )
            return self

        if solver in ["sag", "saga"]:
            max_squared_sum = row_norms(X, squared=True).max()
        else:
            max_squared_sum = None

        if n_classes < 2:
            raise ValueError(
                "This solver needs samples of at least 2 classes"
                " in the data, but the data contains only one"
                " class: %r" % self.classes_[0]
            )

        if self.warm_start:
            warm_start_coef = getattr(self, "coef_", None)
        else:
            warm_start_coef = None
        if warm_start_coef is not None:
            warm_start_coef = move_to(warm_start_coef, xp=np, device="cpu")
            if self.fit_intercept:
                intercept_np = move_to(self.intercept_, xp=np, device="cpu")
                warm_start_coef = np.concatenate(
                    [warm_start_coef, intercept_np[:, None]], axis=1
                )

        # TODO: enable multi-threading if benchmarks show a positive effect,
        # see https://github.com/scikit-learn/scikit-learn/issues/32162
        n_threads = 1

        coefs, _, n_iter = _logistic_regression_path(
            X,
            y,
            classes=self.classes_,
            Cs=[C_],
            l1_ratio=self.l1_ratio,
            fit_intercept=self.fit_intercept,
            tol=self.tol,
            verbose=self.verbose,
            solver=solver,
            max_iter=self.max_iter,
            class_weight=self.class_weight,
            check_input=False,
            random_state=self.random_state,
            coef=warm_start_coef,
            penalty=penalty,
            max_squared_sum=max_squared_sum,
            sample_weight=sample_weight,
            n_threads=n_threads,
        )

        self.n_iter_ = xp.asarray(n_iter, dtype=xp.int32)

        self.coef_ = coefs[0, ...]
        if self.fit_intercept:
            if is_binary:
                self.intercept_ = self.coef_[-1:]
                self.coef_ = self.coef_[:-1][None, :]
            else:
                self.intercept_ = self.coef_[:, -1]
                self.coef_ = self.coef_[:, :-1]
        else:
            if is_binary:
                self.intercept_ = xp.zeros(1, dtype=X.dtype, device=device_)
                self.coef_ = self.coef_[None, :]
            else:
                self.intercept_ = xp.zeros(n_classes, dtype=X.dtype, device=device_)

        return self