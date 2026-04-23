def fit(self, X, y=None):
        """Find clusters based on hierarchical density-based clustering.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features), or \
                ndarray of shape (n_samples, n_samples)
            A feature array, or array of distances between samples if
            `metric='precomputed'`.

        y : None
            Ignored.

        Returns
        -------
        self : object
            Returns self.
        """
        # TODO(1.10): remove "warn" option
        # and leave copy to its default value where applicable in examples and doctests.
        if self.copy == "warn":
            warn(
                "The default value of `copy` will change from False to True in 1.10."
                " Explicitly set a value for `copy` to silence this warning.",
                FutureWarning,
            )
            _copy = False
        else:
            _copy = self.copy

        if self.metric == "precomputed" and self.store_centers is not None:
            raise ValueError(
                "Cannot store centers when using a precomputed distance matrix."
            )

        self._metric_params = self.metric_params or {}
        if self.metric != "precomputed":
            # Non-precomputed matrices may contain non-finite values.
            X = validate_data(
                self,
                X,
                accept_sparse=["csr", "lil"],
                ensure_all_finite=False,
                dtype=np.float64,
            )
            self._raw_data = X
            all_finite = True
            try:
                _assert_all_finite(X.data if issparse(X) else X)
            except ValueError:
                all_finite = False

            if not all_finite:
                # Pass only the purely finite indices into hdbscan
                # We will later assign all non-finite points their
                # corresponding labels, as specified in `_OUTLIER_ENCODING`

                # Reduce X to make the checks for missing/outlier samples more
                # convenient.
                reduced_X = X.sum(axis=1)

                # Samples with missing data are denoted by the presence of
                # `np.nan`
                missing_index = np.isnan(reduced_X).nonzero()[0]

                # Outlier samples are denoted by the presence of `np.inf`
                infinite_index = np.isinf(reduced_X).nonzero()[0]

                # Continue with only finite samples
                finite_index = _get_finite_row_indices(X)
                internal_to_raw = {x: y for x, y in enumerate(finite_index)}
                X = X[finite_index]
        elif issparse(X):
            # Handle sparse precomputed distance matrices separately
            X = validate_data(
                self,
                X,
                accept_sparse=["csr", "lil"],
                dtype=np.float64,
                force_writeable=True,
            )
        else:
            # Only non-sparse, precomputed distance matrices are handled here
            # and thereby allowed to contain numpy.inf for missing distances

            # Perform data validation after removing infinite values (numpy.inf)
            # from the given distance matrix.
            X = validate_data(
                self, X, ensure_all_finite=False, dtype=np.float64, force_writeable=True
            )
            if np.isnan(X).any():
                # TODO: Support np.nan in Cython implementation for precomputed
                # dense HDBSCAN
                raise ValueError("np.nan values found in precomputed-dense")
        if X.shape[0] == 1:
            raise ValueError("n_samples=1 while HDBSCAN requires more than one sample")
        self._min_samples = (
            self.min_cluster_size if self.min_samples is None else self.min_samples
        )

        if self._min_samples > X.shape[0]:
            raise ValueError(
                f"min_samples ({self._min_samples}) must be at most the number of"
                f" samples in X ({X.shape[0]})"
            )

        mst_func = None
        kwargs = dict(
            X=X,
            min_samples=self._min_samples,
            alpha=self.alpha,
            metric=self.metric,
            n_jobs=self.n_jobs,
            **self._metric_params,
        )
        if self.algorithm == "kd_tree" and self.metric not in KDTree.valid_metrics:
            raise ValueError(
                f"{self.metric} is not a valid metric for a KDTree-based algorithm."
                " Please select a different metric."
            )
        elif (
            self.algorithm == "ball_tree" and self.metric not in BallTree.valid_metrics
        ):
            raise ValueError(
                f"{self.metric} is not a valid metric for a BallTree-based algorithm."
                " Please select a different metric."
            )

        if self.algorithm != "auto":
            if (
                self.metric != "precomputed"
                and issparse(X)
                and self.algorithm != "brute"
            ):
                raise ValueError("Sparse data matrices only support algorithm `brute`.")

            if self.algorithm == "brute":
                mst_func = _hdbscan_brute
                kwargs["copy"] = _copy
            elif self.algorithm == "kd_tree":
                mst_func = _hdbscan_prims
                kwargs["algo"] = "kd_tree"
                kwargs["leaf_size"] = self.leaf_size
            else:
                mst_func = _hdbscan_prims
                kwargs["algo"] = "ball_tree"
                kwargs["leaf_size"] = self.leaf_size
        else:
            if issparse(X) or self.metric not in FAST_METRICS:
                # We can't do much with sparse matrices ...
                mst_func = _hdbscan_brute
                kwargs["copy"] = _copy
            elif self.metric in KDTree.valid_metrics:
                # TODO: Benchmark KD vs Ball Tree efficiency
                mst_func = _hdbscan_prims
                kwargs["algo"] = "kd_tree"
                kwargs["leaf_size"] = self.leaf_size
            else:
                # Metric is a valid BallTree metric
                mst_func = _hdbscan_prims
                kwargs["algo"] = "ball_tree"
                kwargs["leaf_size"] = self.leaf_size

        self._single_linkage_tree_ = mst_func(**kwargs)

        self.labels_, self.probabilities_ = tree_to_labels(
            self._single_linkage_tree_,
            self.min_cluster_size,
            self.cluster_selection_method,
            self.allow_single_cluster,
            self.cluster_selection_epsilon,
            self.max_cluster_size,
        )
        if self.metric != "precomputed" and not all_finite:
            # Remap indices to align with original data in the case of
            # non-finite entries. Samples with np.inf are mapped to -1 and
            # those with np.nan are mapped to -2.
            self._single_linkage_tree_ = remap_single_linkage_tree(
                self._single_linkage_tree_,
                internal_to_raw,
                # There may be overlap for points w/ both `np.inf` and `np.nan`
                non_finite=set(np.hstack([infinite_index, missing_index])),
            )
            new_labels = np.empty(self._raw_data.shape[0], dtype=np.int32)
            new_labels[finite_index] = self.labels_
            new_labels[infinite_index] = _OUTLIER_ENCODING["infinite"]["label"]
            new_labels[missing_index] = _OUTLIER_ENCODING["missing"]["label"]
            self.labels_ = new_labels

            new_probabilities = np.zeros(self._raw_data.shape[0], dtype=np.float64)
            new_probabilities[finite_index] = self.probabilities_
            # Infinite outliers have probability 0 by convention, though this
            # is arbitrary.
            new_probabilities[infinite_index] = _OUTLIER_ENCODING["infinite"]["prob"]
            new_probabilities[missing_index] = _OUTLIER_ENCODING["missing"]["prob"]
            self.probabilities_ = new_probabilities

        if self.store_centers:
            self._weighted_cluster_center(X)
        return self