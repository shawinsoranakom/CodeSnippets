def fit(self, X, y=None, sample_weight=None):
        """Fit data X by computing the binning thresholds.

        The last bin is reserved for missing values, whether missing values
        are present in the data or not.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to bin.
        y: None
            Ignored.

        Returns
        -------
        self : object
        """
        if not (3 <= self.n_bins <= 256):
            # min is 3: at least 2 distinct bins and a missing values bin
            raise ValueError(
                "n_bins={} should be no smaller than 3 and no larger than 256.".format(
                    self.n_bins
                )
            )

        X = check_array(X, dtype=[X_DTYPE], ensure_all_finite=False)
        max_bins = self.n_bins - 1
        rng = check_random_state(self.random_state)
        if self.subsample is not None and X.shape[0] > self.subsample:
            subsampling_probabilities = None
            if sample_weight is not None:
                subsampling_probabilities = sample_weight / np.sum(sample_weight)
            # Sampling with replacement to implement frequency semantics
            # for sample weights. Note that we need `replace=True` even when
            # `sample_weight is None` to make sure that passing no weights is
            # statistically equivalent to passing unit weights.
            subset = rng.choice(
                X.shape[0], self.subsample, p=subsampling_probabilities, replace=True
            )
            X = X.take(subset, axis=0)

            # Add a switch to replace sample weights with None
            # since sample weights were already used in subsampling
            # and should not then be propagated to _find_binning_thresholds
            sample_weight = None

        if self.is_categorical is None:
            self.is_categorical_ = np.zeros(X.shape[1], dtype=np.uint8)
        else:
            self.is_categorical_ = np.asarray(self.is_categorical, dtype=np.uint8)

        n_features = X.shape[1]
        known_categories = self.known_categories
        if known_categories is None:
            known_categories = [None] * n_features

        # validate is_categorical and known_categories parameters
        for f_idx in range(n_features):
            is_categorical = self.is_categorical_[f_idx]
            known_cats = known_categories[f_idx]
            if is_categorical and known_cats is None:
                raise ValueError(
                    f"Known categories for feature {f_idx} must be provided."
                )
            if not is_categorical and known_cats is not None:
                raise ValueError(
                    f"Feature {f_idx} isn't marked as a categorical feature, "
                    "but categories were passed."
                )

        self.missing_values_bin_idx_ = self.n_bins - 1

        self.bin_thresholds_ = [None] * n_features
        n_bins_non_missing = [None] * n_features

        non_cat_thresholds = Parallel(n_jobs=self.n_threads, backend="threading")(
            delayed(_find_binning_thresholds)(
                X[:, f_idx], max_bins, sample_weight=sample_weight
            )
            for f_idx in range(n_features)
            if not self.is_categorical_[f_idx]
        )
        non_cat_idx = 0
        for f_idx in range(n_features):
            if self.is_categorical_[f_idx]:
                # Since categories are assumed to be encoded in
                # [0, n_cats] and since n_cats <= max_bins,
                # the thresholds *are* the unique categorical values. This will
                # lead to the correct mapping in transform()
                thresholds = known_categories[f_idx]
                n_bins_non_missing[f_idx] = thresholds.shape[0]
                self.bin_thresholds_[f_idx] = thresholds
            else:
                self.bin_thresholds_[f_idx] = non_cat_thresholds[non_cat_idx]
                n_bins_non_missing[f_idx] = self.bin_thresholds_[f_idx].shape[0] + 1
                non_cat_idx += 1

        self.n_bins_non_missing_ = np.array(n_bins_non_missing, dtype=np.uint32)
        return self