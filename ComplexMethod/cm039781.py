def _get_kernel(self, X, y=None):
        if self.kernel == "rbf":
            if y is None:
                return rbf_kernel(X, X, gamma=self.gamma)
            else:
                return rbf_kernel(X, y, gamma=self.gamma)
        elif self.kernel == "knn":
            if self.nn_fit is None:
                self.nn_fit = NearestNeighbors(
                    n_neighbors=self.n_neighbors, n_jobs=self.n_jobs
                ).fit(X)
            if y is None:
                return self.nn_fit.kneighbors_graph(
                    self.nn_fit._fit_X, self.n_neighbors, mode="connectivity"
                )
            else:
                return self.nn_fit.kneighbors(y, return_distance=False)
        elif callable(self.kernel):
            if y is None:
                return self.kernel(X, X)
            else:
                return self.kernel(X, y)