def fit(self, X, y, sample_weight=None):
        xp, is_array_api_compliant = get_namespace(X, y, sample_weight)

        if self.solver == "lbfgs" and not self.positive:
            raise ValueError(
                "'lbfgs' solver can be used only when positive=True. "
                "Please use another solver."
            )

        if self.positive:
            if self.solver not in ["auto", "lbfgs"]:
                raise ValueError(
                    f"solver='{self.solver}' does not support positive fitting. Please"
                    " set the solver to 'auto' or 'lbfgs', or set `positive=False`"
                )
            else:
                solver = self.solver
        elif sparse.issparse(X) and self.fit_intercept:
            if self.solver not in ["auto", "lbfgs", "lsqr", "sag", "sparse_cg"]:
                raise ValueError(
                    "solver='{}' does not support fitting the intercept "
                    "on sparse data. Please set the solver to 'auto' or "
                    "'lsqr', 'sparse_cg', 'sag', 'lbfgs' "
                    "or set `fit_intercept=False`".format(self.solver)
                )
            if self.solver in ["lsqr", "lbfgs"]:
                solver = self.solver
            elif self.solver == "sag" and self.max_iter is None and self.tol > 1e-4:
                warnings.warn(
                    '"sag" solver requires many iterations to fit '
                    "an intercept with sparse inputs. Either set the "
                    'solver to "auto" or "sparse_cg", or set a low '
                    '"tol" and a high "max_iter" (especially if inputs are '
                    "not standardized)."
                )
                solver = "sag"
            else:
                solver = "sparse_cg"
        else:
            solver = self.solver

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        # when X is sparse we only remove offset from y
        X, y, X_offset, y_offset, X_scale, _ = _preprocess_data(
            X,
            y,
            fit_intercept=self.fit_intercept,
            copy=self.copy_X,
            sample_weight=sample_weight,
            rescale_with_sw=False,
        )

        if solver == "sag" and sparse.issparse(X) and self.fit_intercept:
            self.coef_, self.n_iter_, self.intercept_, self.solver_ = _ridge_regression(
                X,
                y,
                alpha=self.alpha,
                sample_weight=sample_weight,
                max_iter=self.max_iter,
                tol=self.tol,
                solver="sag",
                positive=self.positive,
                random_state=self.random_state,
                return_n_iter=True,
                return_intercept=True,
                return_solver=True,
                check_input=False,
            )
            # add the offset which was subtracted by _preprocess_data
            self.intercept_ += y_offset

        else:
            if sparse.issparse(X) and self.fit_intercept:
                # required to fit intercept with sparse_cg and lbfgs solver
                params = {"X_offset": X_offset, "X_scale": X_scale}
            else:
                # for dense matrices or when intercept is set to 0
                params = {}

            self.coef_, self.n_iter_, self.solver_ = _ridge_regression(
                X,
                y,
                alpha=self.alpha,
                sample_weight=sample_weight,
                max_iter=self.max_iter,
                tol=self.tol,
                solver=solver,
                positive=self.positive,
                random_state=self.random_state,
                return_n_iter=True,
                return_intercept=False,
                return_solver=True,
                check_input=False,
                fit_intercept=self.fit_intercept,
                **params,
            )
            self._set_intercept(X_offset, y_offset, X_scale)

        return self