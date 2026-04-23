def _fit_transform(self, X):
        if self.n_neighbors is not None and self.radius is not None:
            raise ValueError(
                "Both n_neighbors and radius are provided. Use"
                f" Isomap(radius={self.radius}, n_neighbors=None) if intended to use"
                " radius-based neighbors"
            )

        self.nbrs_ = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            radius=self.radius,
            algorithm=self.neighbors_algorithm,
            metric=self.metric,
            p=self.p,
            metric_params=self.metric_params,
            n_jobs=self.n_jobs,
        )
        self.nbrs_.fit(X)
        self.n_features_in_ = self.nbrs_.n_features_in_
        if hasattr(self.nbrs_, "feature_names_in_"):
            self.feature_names_in_ = self.nbrs_.feature_names_in_

        self.kernel_pca_ = KernelPCA(
            n_components=self.n_components,
            kernel="precomputed",
            eigen_solver=self.eigen_solver,
            tol=self.tol,
            max_iter=self.max_iter,
            n_jobs=self.n_jobs,
        ).set_output(transform="default")

        if self.n_neighbors is not None:
            nbg = kneighbors_graph(
                self.nbrs_,
                self.n_neighbors,
                metric=self.metric,
                p=self.p,
                metric_params=self.metric_params,
                mode="distance",
                n_jobs=self.n_jobs,
            )
        else:
            nbg = radius_neighbors_graph(
                self.nbrs_,
                radius=self.radius,
                metric=self.metric,
                p=self.p,
                metric_params=self.metric_params,
                mode="distance",
                n_jobs=self.n_jobs,
            )

        # Compute the number of connected components, and connect the different
        # components to be able to compute a shortest path between all pairs
        # of samples in the graph.
        # Similar fix to cluster._agglomerative._fix_connectivity.
        n_connected_components, labels = connected_components(nbg)
        if n_connected_components > 1:
            if self.metric == "precomputed" and issparse(X):
                raise RuntimeError(
                    "The number of connected components of the neighbors graph"
                    f" is {n_connected_components} > 1. The graph cannot be "
                    "completed with metric='precomputed', and Isomap cannot be"
                    "fitted. Increase the number of neighbors to avoid this "
                    "issue, or precompute the full distance matrix instead "
                    "of passing a sparse neighbors graph."
                )
            warnings.warn(
                (
                    "The number of connected components of the neighbors graph "
                    f"is {n_connected_components} > 1. Completing the graph to fit"
                    " Isomap might be slow. Increase the number of neighbors to "
                    "avoid this issue."
                ),
                stacklevel=2,
            )

            # use array validated by NearestNeighbors
            nbg = _fix_connected_components(
                X=self.nbrs_._fit_X,
                graph=nbg,
                n_connected_components=n_connected_components,
                component_labels=labels,
                mode="distance",
                metric=self.nbrs_.effective_metric_,
                **self.nbrs_.effective_metric_params_,
            )

        _ensure_sparse_index_int32(nbg)
        self.dist_matrix_ = shortest_path(nbg, method=self.path_method, directed=False)

        if self.nbrs_._fit_X.dtype == np.float32:
            self.dist_matrix_ = self.dist_matrix_.astype(
                self.nbrs_._fit_X.dtype, copy=False
            )

        G = self.dist_matrix_**2
        G *= -0.5

        self.embedding_ = self.kernel_pca_.fit_transform(G)
        self._n_features_out = self.embedding_.shape[1]