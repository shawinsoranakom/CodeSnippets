def _global_clustering(self, X=None):
        """
        Global clustering for the subclusters obtained after fitting
        """
        clusterer = self.n_clusters
        centroids = self.subcluster_centers_
        compute_labels = (X is not None) and self.compute_labels

        # Preprocessing for the global clustering.
        not_enough_centroids = False
        if isinstance(clusterer, Integral):
            clusterer = AgglomerativeClustering(n_clusters=self.n_clusters)
            # There is no need to perform the global clustering step.
            if len(centroids) < self.n_clusters:
                not_enough_centroids = True

        # To use in predict to avoid recalculation.
        self._subcluster_norms = row_norms(self.subcluster_centers_, squared=True)

        if clusterer is None or not_enough_centroids:
            self.subcluster_labels_ = np.arange(len(centroids))
            if not_enough_centroids:
                warnings.warn(
                    "Number of subclusters found (%d) by BIRCH is less "
                    "than (%d). Decrease the threshold."
                    % (len(centroids), self.n_clusters),
                    ConvergenceWarning,
                )
        else:
            # The global clustering step that clusters the subclusters of
            # the leaves. It assumes the centroids of the subclusters as
            # samples and finds the final centroids.
            self.subcluster_labels_ = clusterer.fit_predict(self.subcluster_centers_)

        if compute_labels:
            self.labels_ = self._predict(X)