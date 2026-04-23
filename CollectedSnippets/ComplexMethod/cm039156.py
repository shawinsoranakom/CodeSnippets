def _fit(self, X):
        n_sv = self.n_components
        if self.method == "bistochastic":
            normalized_data = _bistochastic_normalize(X)
            n_sv += 1
        elif self.method == "scale":
            normalized_data, _, _ = _scale_normalize(X)
            n_sv += 1
        elif self.method == "log":
            normalized_data = _log_normalize(X)
        n_discard = 0 if self.method == "log" else 1
        u, v = self._svd(normalized_data, n_sv, n_discard)
        ut = u.T
        vt = v.T

        try:
            n_row_clusters, n_col_clusters = self.n_clusters
        except TypeError:
            n_row_clusters = n_col_clusters = self.n_clusters

        best_ut = self._fit_best_piecewise(ut, self.n_best, n_row_clusters)

        best_vt = self._fit_best_piecewise(vt, self.n_best, n_col_clusters)

        self.row_labels_ = self._project_and_cluster(X, best_vt.T, n_row_clusters)

        self.column_labels_ = self._project_and_cluster(X.T, best_ut.T, n_col_clusters)

        self.rows_ = np.vstack(
            [
                self.row_labels_ == label
                for label in range(n_row_clusters)
                for _ in range(n_col_clusters)
            ]
        )
        self.columns_ = np.vstack(
            [
                self.column_labels_ == label
                for _ in range(n_row_clusters)
                for label in range(n_col_clusters)
            ]
        )