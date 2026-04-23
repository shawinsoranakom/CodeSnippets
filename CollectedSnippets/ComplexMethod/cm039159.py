def fit(self, X, y=None):
        """Perform OPTICS clustering.

        Extracts an ordered list of points and reachability distances, and
        performs initial clustering using ``max_eps`` distance specified at
        OPTICS object instantiation.

        Parameters
        ----------
        X : {ndarray, sparse matrix} of shape (n_samples, n_features), or \
                (n_samples, n_samples) if metric='precomputed'
            A feature array, or array of distances between samples if
            metric='precomputed'. If a sparse matrix is provided, it will be
            converted into CSR format.

        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        self : object
            Returns a fitted instance of self.
        """
        dtype = bool if self.metric in PAIRWISE_BOOLEAN_FUNCTIONS else float
        if dtype is bool and X.dtype != bool:
            msg = (
                "Data will be converted to boolean for"
                f" metric {self.metric}, to avoid this warning,"
                " you may convert the data prior to calling fit."
            )
            warnings.warn(msg, DataConversionWarning)

        X = validate_data(self, X, dtype=dtype, accept_sparse="csr")
        if self.metric == "precomputed" and issparse(X):
            X = X.copy()  # copy to avoid in-place modification
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SparseEfficiencyWarning)
                # Set each diagonal to an explicit value so each point is its
                # own neighbor
                X.setdiag(X.diagonal())
        memory = check_memory(self.memory)

        (
            self.ordering_,
            self.core_distances_,
            self.reachability_,
            self.predecessor_,
        ) = memory.cache(compute_optics_graph)(
            X=X,
            min_samples=self.min_samples,
            algorithm=self.algorithm,
            leaf_size=self.leaf_size,
            metric=self.metric,
            metric_params=self.metric_params,
            p=self.p,
            n_jobs=self.n_jobs,
            max_eps=self.max_eps,
        )

        # Extract clusters from the calculated orders and reachability
        if self.cluster_method == "xi":
            labels_, clusters_ = cluster_optics_xi(
                reachability=self.reachability_,
                predecessor=self.predecessor_,
                ordering=self.ordering_,
                min_samples=self.min_samples,
                min_cluster_size=self.min_cluster_size,
                xi=self.xi,
                predecessor_correction=self.predecessor_correction,
            )
            self.cluster_hierarchy_ = clusters_
        elif self.cluster_method == "dbscan":
            if self.eps is None:
                eps = self.max_eps
            else:
                eps = self.eps

            if eps > self.max_eps:
                raise ValueError(
                    "Specify an epsilon smaller than %s. Got %s." % (self.max_eps, eps)
                )

            labels_ = cluster_optics_dbscan(
                reachability=self.reachability_,
                core_distances=self.core_distances_,
                ordering=self.ordering_,
                eps=eps,
            )

        self.labels_ = labels_
        return self