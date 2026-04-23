def fit(self, X, y=None, sample_weight=None):
        """
        Fit the estimator.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to be discretized.

        y : None
            Ignored. This parameter exists only for compatibility with
            :class:`~sklearn.pipeline.Pipeline`.

        sample_weight : ndarray of shape (n_samples,)
            Contains weight values to be associated with each sample.

            .. versionadded:: 1.3

            .. versionchanged:: 1.7
               Added support for strategy="uniform".

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        X = validate_data(self, X, dtype="numeric")

        if self.dtype in (np.float64, np.float32):
            output_dtype = self.dtype
        else:  # self.dtype is None
            output_dtype = X.dtype

        n_samples, n_features = X.shape

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        if self.subsample is not None and n_samples > self.subsample:
            # Take a subsample of `X`
            # When resampling, it is important to subsample **with replacement** to
            # preserve the distribution, in particular in the presence of a few data
            # points with large weights. You can check this by setting `replace=False`
            # in sklearn.utils.test.test_indexing.test_resample_weighted and check that
            # it fails as a justification for this claim.
            X = resample(
                X,
                replace=True,
                n_samples=self.subsample,
                random_state=self.random_state,
                sample_weight=sample_weight,
            )
            # Since we already used the weights when resampling when provided,
            # we set them back to `None` to avoid accounting for the weights twice
            # in subsequent operations to compute weight-aware bin edges with
            # quantiles or k-means.
            sample_weight = None

        n_features = X.shape[1]
        n_bins = self._validate_n_bins(n_features)

        bin_edges = np.zeros(n_features, dtype=object)

        quantile_method = self.quantile_method

        if (
            self.strategy == "quantile"
            and quantile_method not in ["inverted_cdf", "averaged_inverted_cdf"]
            and sample_weight is not None
        ):
            raise ValueError(
                "When fitting with strategy='quantile' and sample weights, "
                "quantile_method should either be set to 'averaged_inverted_cdf' or "
                f"'inverted_cdf', got quantile_method='{quantile_method}' instead."
            )

        if self.strategy != "quantile" and sample_weight is not None:
            # Prepare a mask to filter out zero-weight samples when extracting
            # the min and max values of each columns which are needed for the
            # "uniform" and "kmeans" strategies.
            nnz_weight_mask = sample_weight != 0
        else:
            # Otherwise, all samples are used. Use a slice to avoid creating a
            # new array.
            nnz_weight_mask = slice(None)

        for jj in range(n_features):
            column = X[:, jj]
            col_min = column[nnz_weight_mask].min()
            col_max = column[nnz_weight_mask].max()

            if col_min == col_max:
                warnings.warn(
                    "Feature %d is constant and will be replaced with 0." % jj
                )
                n_bins[jj] = 1
                bin_edges[jj] = np.array([-np.inf, np.inf])
                continue

            if self.strategy == "uniform":
                bin_edges[jj] = np.linspace(col_min, col_max, n_bins[jj] + 1)

            elif self.strategy == "quantile":
                percentile_levels = np.linspace(0, 100, n_bins[jj] + 1)

                # method="linear" is the implicit default for any numpy
                # version. So we keep it version independent in that case by
                # using an empty param dict.
                percentile_kwargs = {}
                if quantile_method != "linear" and sample_weight is None:
                    percentile_kwargs["method"] = quantile_method

                if sample_weight is None:
                    bin_edges[jj] = np.asarray(
                        np.percentile(column, percentile_levels, **percentile_kwargs),
                        dtype=np.float64,
                    )
                else:
                    average = (
                        True if quantile_method == "averaged_inverted_cdf" else False
                    )
                    bin_edges[jj] = _weighted_percentile(
                        column, sample_weight, percentile_levels, average=average
                    )
            elif self.strategy == "kmeans":
                from sklearn.cluster import KMeans  # fixes import loops

                # Deterministic initialization with uniform spacing
                uniform_edges = np.linspace(col_min, col_max, n_bins[jj] + 1)
                init = (uniform_edges[1:] + uniform_edges[:-1])[:, None] * 0.5

                # 1D k-means procedure
                km = KMeans(n_clusters=n_bins[jj], init=init, n_init=1)
                centers = km.fit(
                    column[:, None], sample_weight=sample_weight
                ).cluster_centers_[:, 0]
                # Must sort, centers may be unsorted even with sorted init
                centers.sort()
                bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5
                bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]

            # Remove bins whose width are too small (i.e., <= 1e-8)
            if self.strategy in ("quantile", "kmeans"):
                mask = np.ediff1d(bin_edges[jj], to_begin=np.inf) > 1e-8
                bin_edges[jj] = bin_edges[jj][mask]
                if len(bin_edges[jj]) - 1 != n_bins[jj]:
                    warnings.warn(
                        "Bins whose width are too small (i.e., <= "
                        "1e-8) in feature %d are removed. Consider "
                        "decreasing the number of bins." % jj
                    )
                    n_bins[jj] = len(bin_edges[jj]) - 1

        self.bin_edges_ = bin_edges
        self.n_bins_ = n_bins

        if "onehot" in self.encode:
            self._encoder = OneHotEncoder(
                categories=[np.arange(i) for i in self.n_bins_],
                sparse_output=self.encode == "onehot",
                dtype=output_dtype,
            )
            # Fit the OneHotEncoder with toy datasets
            # so that it's ready for use after the KBinsDiscretizer is fitted
            self._encoder.fit(np.zeros((1, len(self.n_bins_))))

        return self