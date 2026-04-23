def _validate_for_predict(self, X):
        check_is_fitted(self)

        if not callable(self.kernel):
            X = validate_data(
                self,
                X,
                accept_sparse="csr",
                dtype=np.float64,
                order="C",
                accept_large_sparse=False,
                reset=False,
            )

        if self._sparse:
            if not sp.issparse(X):
                X = _align_api_if_sparse(sp.csr_array(X))
            X.sort_indices()

        if sp.issparse(X) and not self._sparse and not callable(self.kernel):
            raise ValueError(
                "cannot use sparse input in %r trained on dense data"
                % type(self).__name__
            )

        if self.kernel == "precomputed":
            if X.shape[1] != self.shape_fit_[0]:
                raise ValueError(
                    "X.shape[1] = %d should be equal to %d, "
                    "the number of samples at training time"
                    % (X.shape[1], self.shape_fit_[0])
                )
        # Fixes https://nvd.nist.gov/vuln/detail/CVE-2020-28975
        # Check that _n_support is consistent with support_vectors
        sv = self.support_vectors_
        if not self._sparse and sv.size > 0 and self.n_support_.sum() != sv.shape[0]:
            raise ValueError(
                f"The internal representation of {self.__class__.__name__} was altered"
            )
        return X