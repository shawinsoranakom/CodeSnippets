def fit(self, X, y=None, sample_weight=None):
        """Compute bisecting k-means clustering.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)

            Training instances to cluster.

            .. note:: The data will be converted to C ordering,
                which will cause a memory copy
                if the given data is not C-contiguous.

        y : Ignored
            Not used, present here for API consistency by convention.

        sample_weight : array-like of shape (n_samples,), default=None
            The weights for each observation in X. If None, all observations
            are assigned equal weight. `sample_weight` is not used during
            initialization if `init` is a callable.

        Returns
        -------
        self
            Fitted estimator.
        """
        X = validate_data(
            self,
            X,
            accept_sparse="csr",
            dtype=[np.float64, np.float32],
            order="C",
            copy=self.copy_x,
            accept_large_sparse=False,
        )

        self._check_params_vs_input(X)

        self._random_state = check_random_state(self.random_state)
        sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)
        self._n_threads = _openmp_effective_n_threads()

        if self.algorithm == "lloyd" or self.n_clusters == 1:
            self._kmeans_single = _kmeans_single_lloyd
            self._check_mkl_vcomp(X, X.shape[0])
        else:
            self._kmeans_single = _kmeans_single_elkan

        # Subtract of mean of X for more accurate distance computations
        if not sp.issparse(X):
            self._X_mean = X.mean(axis=0)
            X -= self._X_mean

        # Initialize the hierarchical clusters tree
        self._bisecting_tree = _BisectingTree(
            indices=np.arange(X.shape[0]),
            center=X.mean(axis=0),
            score=0,
        )

        x_squared_norms = row_norms(X, squared=True)

        for _ in range(self.n_clusters - 1):
            # Chose cluster to bisect
            cluster_to_bisect = self._bisecting_tree.get_cluster_to_bisect()

            # Split this cluster into 2 subclusters
            self._bisect(X, x_squared_norms, sample_weight, cluster_to_bisect)

        # Aggregate final labels and centers from the bisecting tree
        self.labels_ = np.full(X.shape[0], -1, dtype=np.int32)
        self.cluster_centers_ = np.empty((self.n_clusters, X.shape[1]), dtype=X.dtype)

        for i, cluster_node in enumerate(self._bisecting_tree.iter_leaves()):
            self.labels_[cluster_node.indices] = i
            self.cluster_centers_[i] = cluster_node.center
            cluster_node.label = i  # label final clusters for future prediction
            cluster_node.indices = None  # release memory

        # Restore original data
        if not sp.issparse(X):
            X += self._X_mean
            self.cluster_centers_ += self._X_mean

        _inertia = _inertia_sparse if sp.issparse(X) else _inertia_dense
        self.inertia_ = _inertia(
            X, sample_weight, self.cluster_centers_, self.labels_, self._n_threads
        )

        self._n_features_out = self.cluster_centers_.shape[0]

        return self