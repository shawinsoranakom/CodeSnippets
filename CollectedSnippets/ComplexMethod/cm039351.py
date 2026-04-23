def _get_affinity_matrix(self, X, Y=None):
        """Calculate the affinity matrix from data
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples
            and `n_features` is the number of features.

            If affinity is "precomputed"
            X : array-like of shape (n_samples, n_samples),
            Interpret X as precomputed adjacency graph computed from
            samples.

        Y: Ignored

        Returns
        -------
        affinity_matrix of shape (n_samples, n_samples)
        """
        if self.affinity == "precomputed":
            self.affinity_matrix_ = X
            return self.affinity_matrix_
        if self.affinity == "precomputed_nearest_neighbors":
            estimator = NearestNeighbors(
                n_neighbors=self.n_neighbors, n_jobs=self.n_jobs, metric="precomputed"
            ).fit(X)
            connectivity = estimator.kneighbors_graph(X=X, mode="connectivity")
            self.affinity_matrix_ = 0.5 * (connectivity + connectivity.T)
            return self.affinity_matrix_
        if self.affinity == "nearest_neighbors":
            if sparse.issparse(X):
                warnings.warn(
                    "Nearest neighbors affinity currently does "
                    "not support sparse input, falling back to "
                    "rbf affinity"
                )
                self.affinity = "rbf"
            else:
                self.n_neighbors_ = (
                    self.n_neighbors
                    if self.n_neighbors is not None
                    else max(int(X.shape[0] / 10), 1)
                )
                self.affinity_matrix_ = kneighbors_graph(
                    X, self.n_neighbors_, include_self=True, n_jobs=self.n_jobs
                )
                # currently only symmetric affinity_matrix supported
                self.affinity_matrix_ = 0.5 * (
                    self.affinity_matrix_ + self.affinity_matrix_.T
                )
                return self.affinity_matrix_
        if self.affinity == "rbf":
            self.gamma_ = self.gamma if self.gamma is not None else 1.0 / X.shape[1]
            self.affinity_matrix_ = rbf_kernel(X, gamma=self.gamma_)
            return self.affinity_matrix_
        self.affinity_matrix_ = self.affinity(X)
        return self.affinity_matrix_