def transform(self, X):
        """Generate the feature map approximation for X.

        Parameters
        ----------
        X : {array-like}, shape (n_samples, n_features)
            New data, where `n_samples` is the number of samples
            and `n_features` is the number of features.

        Returns
        -------
        X_new : array-like, shape (n_samples, n_components)
            Returns the instance itself.
        """

        check_is_fitted(self)
        X = validate_data(self, X, accept_sparse="csc", reset=False)

        X_gamma = np.sqrt(self.gamma) * X

        if sp.issparse(X_gamma) and self.coef0 != 0:
            X_gamma = sp.hstack(
                [X_gamma, np.sqrt(self.coef0) * np.ones((X_gamma.shape[0], 1))],
                format="csc",
            )

        elif not sp.issparse(X_gamma) and self.coef0 != 0:
            X_gamma = np.hstack(
                [X_gamma, np.sqrt(self.coef0) * np.ones((X_gamma.shape[0], 1))]
            )

        if X_gamma.shape[1] != self.indexHash_.shape[1]:
            raise ValueError(
                "Number of features of test samples does not"
                " match that of training samples."
            )

        count_sketches = np.zeros((X_gamma.shape[0], self.degree, self.n_components))

        if sp.issparse(X_gamma):
            for j in range(X_gamma.shape[1]):
                for d in range(self.degree):
                    iHashIndex = self.indexHash_[d, j]
                    iHashBit = self.bitHash_[d, j]
                    count_sketches[:, d, iHashIndex] += (
                        (iHashBit * X_gamma[:, [j]]).toarray().ravel()
                    )

        else:
            for j in range(X_gamma.shape[1]):
                for d in range(self.degree):
                    iHashIndex = self.indexHash_[d, j]
                    iHashBit = self.bitHash_[d, j]
                    count_sketches[:, d, iHashIndex] += iHashBit * X_gamma[:, j]

        # For each same, compute a count sketch of phi(x) using the polynomial
        # multiplication (via FFT) of p count sketches of x.
        count_sketches_fft = fft(count_sketches, axis=2, overwrite_x=True)
        count_sketches_fft_prod = np.prod(count_sketches_fft, axis=1)
        data_sketch = np.real(ifft(count_sketches_fft_prod, overwrite_x=True))

        return data_sketch