def _fit(
        self,
        X,
        y,
        alpha,
        loss,
        learning_rate,
        coef_init=None,
        intercept_init=None,
        sample_weight=None,
    ):
        if self.warm_start and getattr(self, "coef_", None) is not None:
            if coef_init is None:
                coef_init = self.coef_
            if intercept_init is None:
                intercept_init = self.intercept_
        else:
            self.coef_ = None
            self.intercept_ = None

        # Clear iteration count for multiple call to fit.
        self.t_ = 1.0

        self._partial_fit(
            X,
            y,
            alpha,
            loss,
            learning_rate,
            self.max_iter,
            sample_weight,
            coef_init,
            intercept_init,
        )

        if (
            self.tol is not None
            and self.tol > -np.inf
            and self.n_iter_ == self.max_iter
        ):
            warnings.warn(
                (
                    "Maximum number of iteration reached before "
                    "convergence. Consider increasing max_iter to "
                    "improve the fit."
                ),
                ConvergenceWarning,
            )

        if self.power_t < 0:
            warnings.warn(
                "Negative values for `power_t` are deprecated in version 1.8 "
                "and will raise an error in 1.10. "
                "Use values in the range [0.0, inf) instead.",
                FutureWarning,
            )

        return self