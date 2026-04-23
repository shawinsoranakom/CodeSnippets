def fit_transform(self, X, y=None, init=None):
        """
        Fit the data from `X`, and returns the embedded coordinates.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features) or \
                (n_samples, n_samples)
            Input data. If ``metric=='precomputed'``, the input should
            be the dissimilarity matrix.

        y : Ignored
            Not used, present for API consistency by convention.

        init : ndarray of shape (n_samples, n_components), default=None
            Starting configuration of the embedding to initialize the SMACOF
            algorithm. By default, the algorithm is initialized with a randomly
            chosen array.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            X transformed in the new space.
        """

        if self.init == "warn":
            warnings.warn(
                "The default value of `init` will change from 'random' to "
                "'classical_mds' in 1.10. To suppress this warning, provide "
                "some value of `init`.",
                FutureWarning,
            )
            self._init = "random"
        else:
            self._init = self.init

        if self.dissimilarity != "deprecated":
            if not isinstance(self.metric, bool) and self.metric != "euclidean":
                raise ValueError(
                    "You provided both `dissimilarity` and `metric`. Please use "
                    "only `metric`."
                )
            else:
                warnings.warn(
                    "The `dissimilarity` parameter is deprecated and will be "
                    "removed in 1.10. Use `metric` instead.",
                    FutureWarning,
                )
                self._metric = self.dissimilarity

        if isinstance(self.metric, bool):
            warnings.warn(
                f"Use metric_mds={self.metric} instead of metric={self.metric}. The "
                "support for metric={True/False} will be dropped in 1.10.",
                FutureWarning,
            )
            if self.dissimilarity == "deprecated":
                self._metric = "euclidean"
            self._metric_mds = self.metric
        else:
            if self.dissimilarity == "deprecated":
                self._metric = self.metric
            self._metric_mds = self.metric_mds

        X = validate_data(self, X)
        if X.shape[0] == X.shape[1] and self._metric != "precomputed":
            warnings.warn(
                "The provided input is a square matrix. Note that ``fit`` constructs "
                "a dissimilarity matrix from data and will treat rows as samples "
                "and columns as features. To use a pre-computed dissimilarity matrix, "
                "set ``metric='precomputed'``."
            )

        if self._metric == "precomputed":
            self.dissimilarity_matrix_ = X
            self.dissimilarity_matrix_ = check_symmetric(
                self.dissimilarity_matrix_, raise_exception=True
            )
        else:
            self.dissimilarity_matrix_ = pairwise_distances(
                X,
                metric=self._metric,
                **(self.metric_params if self.metric_params is not None else {}),
            )

        if init is not None:
            init_array = init
        elif self._init == "classical_mds":
            cmds = ClassicalMDS(metric="precomputed", n_components=self.n_components)
            init_array = cmds.fit_transform(self.dissimilarity_matrix_)
        else:
            init_array = None

        self.embedding_, self.stress_, self.n_iter_ = smacof(
            self.dissimilarity_matrix_,
            metric=self._metric_mds,
            n_components=self.n_components,
            init=init_array,
            n_init=self.n_init,
            n_jobs=self.n_jobs,
            max_iter=self.max_iter,
            verbose=self.verbose,
            eps=self.eps,
            random_state=self.random_state,
            return_n_iter=True,
            normalized_stress=self.normalized_stress,
        )

        return self.embedding_