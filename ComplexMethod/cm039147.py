def _check_w_h(self, X, W, H, update_H):
        """Check W and H, or initialize them."""
        n_samples, n_features = X.shape

        if self.init == "custom" and update_H:
            _check_init(H, (self._n_components, n_features), "NMF (input H)")
            _check_init(W, (n_samples, self._n_components), "NMF (input W)")
            if self._n_components == "auto":
                self._n_components = H.shape[0]

            if H.dtype != X.dtype or W.dtype != X.dtype:
                raise TypeError(
                    "H and W should have the same dtype as X. Got "
                    "H.dtype = {} and W.dtype = {}.".format(H.dtype, W.dtype)
                )

        elif not update_H:
            if W is not None:
                warnings.warn(
                    "When update_H=False, the provided initial W is not used.",
                    RuntimeWarning,
                )

            _check_init(H, (self._n_components, n_features), "NMF (input H)")
            if self._n_components == "auto":
                self._n_components = H.shape[0]

            if H.dtype != X.dtype:
                raise TypeError(
                    "H should have the same dtype as X. Got H.dtype = {}.".format(
                        H.dtype
                    )
                )

            # 'mu' solver should not be initialized by zeros
            if self.solver == "mu":
                avg = np.sqrt(X.mean() / self._n_components)
                W = np.full((n_samples, self._n_components), avg, dtype=X.dtype)
            else:
                W = np.zeros((n_samples, self._n_components), dtype=X.dtype)

        else:
            if W is not None or H is not None:
                warnings.warn(
                    (
                        "When init!='custom', provided W or H are ignored. Set "
                        " init='custom' to use them as initialization."
                    ),
                    RuntimeWarning,
                )

            if self._n_components == "auto":
                self._n_components = X.shape[1]

            W, H = _initialize_nmf(
                X, self._n_components, init=self.init, random_state=self.random_state
            )

        return W, H