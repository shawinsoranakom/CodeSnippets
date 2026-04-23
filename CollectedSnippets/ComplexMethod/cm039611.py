def fit(self, X, y, sample_weight=None):
        """Fit a Generalized Linear Model.

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
            Fitted model.
        """
        xp, _, device_ = get_namespace_and_device(X)
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csc", "csr"],
            dtype=[xp.float64, xp.float32],
            y_numeric=True,
            multi_output=False,
        )
        loss_dtype = X.dtype
        y = check_array(y, dtype=loss_dtype, order="C", ensure_2d=False)

        if sample_weight is not None:
            # Note that _check_sample_weight calls check_array(order="C") required by
            # losses.
            sample_weight = _check_sample_weight(sample_weight, X, dtype=loss_dtype)

        y, sample_weight = move_to(y, sample_weight, xp=xp, device=device_)

        n_samples, n_features = X.shape
        self._base_loss = self._get_loss(xp=xp, device=device_)

        linear_loss = LinearModelLoss(
            base_loss=self._base_loss,
            fit_intercept=self.fit_intercept,
        )

        if not linear_loss.base_loss.in_y_true_range(y):
            raise ValueError(
                "Some value(s) of y are out of the valid range of the loss"
                f" {self._base_loss.__class__.__name__!r}."
            )

        # TODO: if alpha=0 check that X is not rank deficient

        # NOTE: Rescaling of sample_weight:
        # We want to minimize
        #     obj = 1/(2 * sum(sample_weight)) * sum(sample_weight * deviance)
        #         + 1/2 * alpha * L2,
        # with
        #     deviance = 2 * loss.
        # The objective is invariant to multiplying sample_weight by a constant. We
        # could choose this constant such that sum(sample_weight) = 1 in order to end
        # up with
        #     obj = sum(sample_weight * loss) + 1/2 * alpha * L2.
        # But LinearModelLoss.loss() already computes
        #     average(loss, weights=sample_weight)
        # Thus, without rescaling, we have
        #     obj = LinearModelLoss.loss(...)

        loss_dtype_np = _matching_numpy_dtype(X, xp=xp)
        if self.warm_start and hasattr(self, "coef_"):
            coef_xp, _ = get_namespace(self.coef_)
            coef = move_to(self.coef_, xp=np, device="cpu")
            if self.fit_intercept:
                # LinearModelLoss needs intercept at the end of coefficient array.
                intercept = move_to(self.intercept_, xp=np, device="cpu")
                coef = np.concatenate((coef, np.array([intercept])))
            coef = coef.astype(loss_dtype_np, copy=False)
        else:
            coef = linear_loss.init_zero_coef(X, dtype=loss_dtype_np)
            if self.fit_intercept:
                coef[-1] = linear_loss.base_loss.link.link(
                    _average(y, weights=sample_weight)
                )

        l2_reg_strength = self.alpha
        n_threads = _openmp_effective_n_threads()

        # Algorithms for optimization:
        # Note again that our losses implement 1/2 * deviance.
        if self.solver == "lbfgs":
            func = linear_loss.loss_gradient

            opt_res = scipy.optimize.minimize(
                func,
                coef,
                method="L-BFGS-B",
                jac=True,
                options={
                    "maxiter": self.max_iter,
                    "maxls": 50,  # default is 20
                    "gtol": self.tol,
                    # The constant 64 was found empirically to pass the test suite.
                    # The point is that ftol is very small, but a bit larger than
                    # machine precision for float64, which is the dtype used by lbfgs.
                    "ftol": 64 * np.finfo(float).eps,
                    **_get_additional_lbfgs_options_dict("iprint", self.verbose - 1),
                },
                args=(X, y, sample_weight, l2_reg_strength, n_threads),
            )
            self.n_iter_ = _check_optimize_result(
                "lbfgs", opt_res, max_iter=self.max_iter
            )
            coef = opt_res.x
            coef = xp.asarray(
                coef.copy(order="C" if not _is_numpy_namespace(xp) else "K"),
                dtype=X.dtype,
                device=device_,
            )
        elif self.solver == "newton-cholesky":
            sol = NewtonCholeskySolver(
                coef=coef,
                linear_loss=linear_loss,
                l2_reg_strength=l2_reg_strength,
                tol=self.tol,
                max_iter=self.max_iter,
                n_threads=n_threads,
                verbose=self.verbose,
            )
            coef = sol.solve(X, y, sample_weight)
            self.n_iter_ = sol.iteration
        elif issubclass(self.solver, NewtonSolver):
            sol = self.solver(
                coef=coef,
                linear_loss=linear_loss,
                l2_reg_strength=l2_reg_strength,
                tol=self.tol,
                max_iter=self.max_iter,
                n_threads=n_threads,
            )
            coef = sol.solve(X, y, sample_weight)
            self.n_iter_ = sol.iteration
        else:
            raise ValueError(f"Invalid solver={self.solver}.")

        if self.fit_intercept:
            self.intercept_ = coef[-1]
            self.coef_ = coef[:-1]
        else:
            # set intercept to zero as the other linear models do
            self.intercept_ = 0.0
            self.coef_ = coef

        return self