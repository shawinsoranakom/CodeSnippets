def _check_params_vs_input(self, X, default_n_init=None):
        # n_clusters
        if X.shape[0] < self.n_clusters:
            raise ValueError(
                f"n_samples={X.shape[0]} should be >= n_clusters={self.n_clusters}."
            )

        # tol
        self._tol = _tolerance(X, self.tol)

        # n-init
        if self.n_init == "auto":
            if isinstance(self.init, str) and self.init == "k-means++":
                self._n_init = 1
            elif isinstance(self.init, str) and self.init == "random":
                self._n_init = default_n_init
            elif callable(self.init):
                self._n_init = default_n_init
            else:  # array-like
                self._n_init = 1
        else:
            self._n_init = self.n_init

        if _is_arraylike_not_scalar(self.init) and self._n_init != 1:
            warnings.warn(
                (
                    "Explicit initial center position passed: performing only"
                    f" one init in {self.__class__.__name__} instead of "
                    f"n_init={self._n_init}."
                ),
                RuntimeWarning,
                stacklevel=2,
            )
            self._n_init = 1