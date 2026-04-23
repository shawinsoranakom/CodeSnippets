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
        if hasattr(self, "classes_"):
            # delete the attribute otherwise _partial_fit thinks it's not the first call
            delattr(self, "classes_")

        # labels can be encoded as float, int, or string literals
        # np.unique sorts in asc order; largest class id is positive class
        y = validate_data(self, y=y)
        classes = np.unique(y)

        if self.warm_start and hasattr(self, "coef_"):
            if coef_init is None:
                coef_init = self.coef_
            if intercept_init is None:
                intercept_init = self.intercept_
        else:
            self.coef_ = None
            self.intercept_ = None

        if self.average > 0:
            self._standard_coef = self.coef_
            self._standard_intercept = self.intercept_
            self._average_coef = None
            self._average_intercept = None

        # Clear iteration count for multiple call to fit.
        self.t_ = 1.0

        self._partial_fit(
            X,
            y,
            alpha,
            loss,
            learning_rate,
            self.max_iter,
            classes,
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