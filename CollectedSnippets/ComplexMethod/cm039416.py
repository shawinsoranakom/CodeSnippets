def fit(self, X, y=None, sample_weight=None):
        """
        Fit estimator.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The input samples. Use ``dtype=np.float32`` for maximum
            efficiency. Sparse matrices are also supported, use sparse
            ``csc_matrix`` for maximum efficiency.

        y : Ignored
            Not used, present for API consistency by convention.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights. If None, then samples are equally weighted.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        X = validate_data(
            self, X, accept_sparse=["csc"], dtype=tree_dtype, ensure_all_finite=False
        )

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=None)

        if issparse(X):
            # Pre-sort indices to avoid that each individual tree of the
            # ensemble sorts the indices.
            X.sort_indices()

        rnd = check_random_state(self.random_state)
        y = rnd.uniform(size=X.shape[0])

        # ensure that max_sample is in [1, n_samples]:
        n_samples = X.shape[0]

        if isinstance(self.max_samples, str) and self.max_samples == "auto":
            max_samples = min(256, n_samples)

        elif isinstance(self.max_samples, numbers.Integral):
            if self.max_samples > n_samples:
                warn(
                    "max_samples (%s) is greater than the "
                    "total number of samples (%s). max_samples "
                    "will be set to n_samples for estimation."
                    % (self.max_samples, n_samples)
                )
                max_samples = n_samples
            else:
                max_samples = self.max_samples
        else:  # max_samples is float
            max_samples = int(self.max_samples * X.shape[0])

        self.max_samples_ = max_samples
        max_depth = int(np.ceil(np.log2(max(max_samples, 2))))
        super()._fit(
            X,
            y,
            max_samples=max_samples,
            max_depth=max_depth,
            sample_weight=sample_weight,
            check_input=False,
        )

        self._average_path_length_per_tree, self._decision_path_lengths = zip(
            *[
                (
                    _average_path_length(tree.tree_.n_node_samples),
                    tree.tree_.compute_node_depths(),
                )
                for tree in self.estimators_
            ]
        )

        if self.contamination == "auto":
            # 0.5 plays a special role as described in the original paper.
            # we take the opposite as we consider the opposite of their score.
            self.offset_ = -0.5
            return self

        # Else, define offset_ wrt contamination parameter
        # To avoid performing input validation a second time we call
        # _score_samples rather than score_samples.
        # _score_samples expects a CSR matrix, so we convert if necessary.
        if issparse(X):
            X = X.tocsr()
        self.offset_ = np.percentile(self._score_samples(X), 100.0 * self.contamination)

        return self