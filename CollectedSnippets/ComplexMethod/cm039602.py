def fit(self, X, y, sample_weight=None):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,)
            Target values.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights.

        Returns
        -------
        self : object
            Returns self.
        """
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csc", "csr", "coo"],
            y_numeric=True,
            multi_output=False,
        )
        sample_weight = _check_sample_weight(sample_weight, X)

        n_features = X.shape[1]
        n_params = n_features

        if self.fit_intercept:
            n_params += 1
            # Note that centering y and X with _preprocess_data does not work
            # for quantile regression.

        # The objective is defined as 1/n * sum(pinball loss) + alpha * L1.
        # So we rescale the penalty term, which is equivalent.
        alpha = np.sum(sample_weight) * self.alpha

        if self.solver == "interior-point" and sp_version >= parse_version("1.11.0"):
            raise ValueError(
                f"Solver {self.solver} is not anymore available in SciPy >= 1.11.0."
            )

        if sparse.issparse(X) and self.solver not in ["highs", "highs-ds", "highs-ipm"]:
            raise ValueError(
                f"Solver {self.solver} does not support sparse X. "
                "Use solver 'highs' for example."
            )
        # make default solver more stable
        if self.solver_options is None and self.solver == "interior-point":
            solver_options = {"lstsq": True}
        else:
            solver_options = self.solver_options

        # After rescaling alpha, the minimization problem is
        #     min sum(pinball loss) + alpha * L1
        # Use linear programming formulation of quantile regression
        #     min_x c x
        #           A_eq x = b_eq
        #                0 <= x
        # x = (s0, s, t0, t, u, v) = slack variables >= 0
        # intercept = s0 - t0
        # coef = s - t
        # c = (0, alpha * 1_p, 0, alpha * 1_p, quantile * 1_n, (1-quantile) * 1_n)
        # residual = y - X@coef - intercept = u - v
        # A_eq = (1_n, X, -1_n, -X, diag(1_n), -diag(1_n))
        # b_eq = y
        # p = n_features
        # n = n_samples
        # 1_n = vector of length n with entries equal one
        # see https://stats.stackexchange.com/questions/384909/
        #
        # Filtering out zero sample weights from the beginning makes life
        # easier for the linprog solver.
        indices = np.nonzero(sample_weight)[0]
        n_indices = len(indices)  # use n_mask instead of n_samples
        if n_indices < len(sample_weight):
            sample_weight = sample_weight[indices]
            X = _safe_indexing(X, indices)
            y = _safe_indexing(y, indices)
        c = np.concatenate(
            [
                np.full(2 * n_params, fill_value=alpha),
                sample_weight * self.quantile,
                sample_weight * (1 - self.quantile),
            ]
        )
        if self.fit_intercept:
            # do not penalize the intercept
            c[0] = 0
            c[n_params] = 0

        if self.solver in ["highs", "highs-ds", "highs-ipm"]:
            # Note that highs methods always use a sparse CSC memory layout internally,
            # even for optimization problems parametrized using dense numpy arrays.
            # Therefore, we work with CSC matrices as early as possible to limit
            # unnecessary repeated memory copies.
            eye = _sparse_eye_array(n_indices, dtype=X.dtype, format="csc")
            if self.fit_intercept:
                ones = sparse.csc_array(np.ones(shape=(n_indices, 1), dtype=X.dtype))
                A_eq = sparse.hstack([ones, X, -ones, -X, eye, -eye], format="csc")
            else:
                A_eq = sparse.hstack([X, -X, eye, -eye], format="csc")
        else:
            eye = np.eye(n_indices)
            if self.fit_intercept:
                ones = np.ones((n_indices, 1))
                A_eq = np.concatenate([ones, X, -ones, -X, eye, -eye], axis=1)
            else:
                A_eq = np.concatenate([X, -X, eye, -eye], axis=1)

        b_eq = y

        result = linprog(
            c=c,
            A_eq=A_eq,
            b_eq=b_eq,
            method=self.solver,
            options=solver_options,
        )
        solution = result.x
        if not result.success:
            failure = {
                1: "Iteration limit reached.",
                2: "Problem appears to be infeasible.",
                3: "Problem appears to be unbounded.",
                4: "Numerical difficulties encountered.",
            }
            warnings.warn(
                "Linear programming for QuantileRegressor did not succeed.\n"
                f"Status is {result.status}: "
                + failure.setdefault(result.status, "unknown reason")
                + "\n"
                + "Result message of linprog:\n"
                + result.message,
                ConvergenceWarning,
            )

        # positive slack - negative slack
        # solution is an array with (params_pos, params_neg, u, v)
        params = solution[:n_params] - solution[n_params : 2 * n_params]

        self.n_iter_ = result.nit

        if self.fit_intercept:
            self.coef_ = params[1:]
            self.intercept_ = params[0]
        else:
            self.coef_ = params
            self.intercept_ = 0.0
        return self