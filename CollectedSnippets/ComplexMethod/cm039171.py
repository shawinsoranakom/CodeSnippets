def fit(self, X, y=None):
        """Perform spectral clustering from features, or affinity matrix.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features) or \
                (n_samples, n_samples)
            Training instances to cluster, similarities / affinities between
            instances if ``affinity='precomputed'``, or distances between
            instances if ``affinity='precomputed_nearest_neighbors``. If a
            sparse matrix is provided in a format other than ``csr_matrix``,
            ``csc_matrix``, or ``coo_matrix``, it will be converted into a
            sparse ``csr_matrix``.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            A fitted instance of the estimator.
        """
        X = validate_data(
            self,
            X,
            accept_sparse=["csr", "csc", "coo"],
            dtype=np.float64,
            ensure_min_samples=2,
        )
        allow_squared = self.affinity in [
            "precomputed",
            "precomputed_nearest_neighbors",
        ]
        if X.shape[0] == X.shape[1] and not allow_squared:
            warnings.warn(
                "The spectral clustering API has changed. ``fit``"
                "now constructs an affinity matrix from data. To use"
                " a custom affinity matrix, "
                "set ``affinity=precomputed``."
            )

        if self.affinity == "nearest_neighbors":
            connectivity = kneighbors_graph(
                X, n_neighbors=self.n_neighbors, include_self=True, n_jobs=self.n_jobs
            )
            self.affinity_matrix_ = 0.5 * (connectivity + connectivity.T)
        elif self.affinity == "precomputed_nearest_neighbors":
            estimator = NearestNeighbors(
                n_neighbors=self.n_neighbors, n_jobs=self.n_jobs, metric="precomputed"
            ).fit(X)
            connectivity = estimator.kneighbors_graph(X=X, mode="connectivity")
            self.affinity_matrix_ = 0.5 * (connectivity + connectivity.T)
        elif self.affinity == "precomputed":
            self.affinity_matrix_ = X
        else:
            params = self.kernel_params
            if params is None:
                params = {}
            if not callable(self.affinity):
                params["gamma"] = self.gamma
                params["degree"] = self.degree
                params["coef0"] = self.coef0
            self.affinity_matrix_ = pairwise_kernels(
                X, metric=self.affinity, filter_params=True, **params
            )

        random_state = check_random_state(self.random_state)
        n_components = (
            self.n_clusters if self.n_components is None else self.n_components
        )
        # We now obtain the real valued solution matrix to the
        # relaxed Ncut problem, solving the eigenvalue problem
        # L_sym x = lambda x  and recovering u = D^-1/2 x.
        # The first eigenvector is constant only for fully connected graphs
        # and should be kept for spectral clustering (drop_first = False)
        # See spectral_embedding documentation.
        maps = _spectral_embedding(
            self.affinity_matrix_,
            n_components=n_components,
            eigen_solver=self.eigen_solver,
            random_state=random_state,
            eigen_tol=self.eigen_tol,
            drop_first=False,
        )
        if self.verbose:
            print(f"Computing label assignment using {self.assign_labels}")

        if self.assign_labels == "kmeans":
            _, self.labels_, _ = k_means(
                maps,
                self.n_clusters,
                random_state=random_state,
                n_init=self.n_init,
                verbose=self.verbose,
            )
        elif self.assign_labels == "cluster_qr":
            self.labels_ = cluster_qr(maps)
        else:
            self.labels_ = discretize(maps, random_state=random_state)

        return self