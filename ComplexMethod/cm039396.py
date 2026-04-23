def fit(self, X, y):
        """
        Fit the NearestCentroid model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.
            Note that centroid shrinking cannot be used with sparse matrices.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        # If X is sparse and the metric is "manhattan", store it in a csc
        # format is easier to calculate the median.
        if self.metric == "manhattan":
            X, y = validate_data(self, X, y, accept_sparse=["csc"])
        else:
            ensure_all_finite = (
                "allow-nan" if get_tags(self).input_tags.allow_nan else True
            )
            X, y = validate_data(
                self,
                X,
                y,
                ensure_all_finite=ensure_all_finite,
                accept_sparse=["csr", "csc"],
            )
        is_X_sparse = sp.issparse(X)
        check_classification_targets(y)

        n_samples, n_features = X.shape
        le = LabelEncoder()
        y_ind = le.fit_transform(y)
        self.classes_ = classes = le.classes_
        n_classes = classes.size
        if n_classes < 2:
            raise ValueError(
                "The number of classes has to be greater than one; got %d class"
                % (n_classes)
            )

        if self.priors == "empirical":  # estimate priors from sample
            _, class_counts = np.unique(y, return_inverse=True)  # non-negative ints
            self.class_prior_ = np.bincount(class_counts) / float(len(y))
        elif self.priors == "uniform":
            self.class_prior_ = np.asarray([1 / n_classes] * n_classes)
        else:
            self.class_prior_ = np.asarray(self.priors)

        if (self.class_prior_ < 0).any():
            raise ValueError("priors must be non-negative")
        if not np.isclose(self.class_prior_.sum(), 1.0):
            warnings.warn(
                "The priors do not sum to 1. Normalizing such that it sums to one.",
                UserWarning,
            )
            self.class_prior_ = self.class_prior_ / self.class_prior_.sum()

        # Mask mapping each class to its members.
        self.centroids_ = np.empty((n_classes, n_features), dtype=np.float64)

        # Number of clusters in each class.
        nk = np.zeros(n_classes)

        for cur_class in range(n_classes):
            center_mask = y_ind == cur_class
            nk[cur_class] = np.sum(center_mask)
            if is_X_sparse:
                center_mask = np.where(center_mask)[0]

            if self.metric == "manhattan":
                # NumPy does not calculate median of sparse matrices.
                if not is_X_sparse:
                    self.centroids_[cur_class] = np.median(X[center_mask], axis=0)
                else:
                    self.centroids_[cur_class] = csc_median_axis_0(X[center_mask])
            else:  # metric == "euclidean"
                self.centroids_[cur_class] = X[center_mask].mean(axis=0)

        # Compute within-class std_dev with unshrunked centroids
        variance = np.array(X - self.centroids_[y_ind], copy=False) ** 2
        self.within_class_std_dev_ = np.array(
            np.sqrt(variance.sum(axis=0) / (n_samples - n_classes)), copy=False
        )
        if any(self.within_class_std_dev_ == 0):
            warnings.warn(
                "self.within_class_std_dev_ has at least 1 zero standard deviation."
                "Inputs within the same classes for at least 1 feature are identical."
            )

        err_msg = "All features have zero variance. Division by zero."
        if is_X_sparse and np.all((X.max(axis=0) - X.min(axis=0)).toarray() == 0):
            raise ValueError(err_msg)
        elif not is_X_sparse and np.all(np.ptp(X, axis=0) == 0):
            raise ValueError(err_msg)

        dataset_centroid_ = X.mean(axis=0)
        # m parameter for determining deviation
        m = np.sqrt((1.0 / nk) - (1.0 / n_samples))
        # Calculate deviation using the standard deviation of centroids.
        # To deter outliers from affecting the results.
        s = self.within_class_std_dev_ + np.median(self.within_class_std_dev_)
        mm = m.reshape(len(m), 1)  # Reshape to allow broadcasting.
        ms = mm * s
        self.deviations_ = np.array(
            (self.centroids_ - dataset_centroid_) / ms, copy=False
        )
        # Soft thresholding: if the deviation crosses 0 during shrinking,
        # it becomes zero.
        if self.shrink_threshold:
            signs = np.sign(self.deviations_)
            self.deviations_ = np.abs(self.deviations_) - self.shrink_threshold
            np.clip(self.deviations_, 0, None, out=self.deviations_)
            self.deviations_ *= signs
            # Now adjust the centroids using the deviation
            msd = ms * self.deviations_
            self.centroids_ = np.array(dataset_centroid_ + msd, copy=False)
        return self