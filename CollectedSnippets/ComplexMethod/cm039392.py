def predict_proba(self, X):
        """Return probability estimates for the test data X.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_queries, n_features), \
                or (n_queries, n_indexed) if metric == 'precomputed', or None
            Test samples. If `None`, predictions for all indexed points are
            returned; in this case, points are not considered their own
            neighbors.

        Returns
        -------
        p : ndarray of shape (n_queries, n_classes), or a list of \
                n_outputs of such arrays if n_outputs > 1.
            The class probabilities of the input samples. Classes are ordered
            by lexicographic order.
        """
        check_is_fitted(self, "_fit_method")
        n_queries = _num_samples(self._fit_X if X is None else X)

        metric, metric_kwargs = _adjusted_metric(
            metric=self.metric, metric_kwargs=self.metric_params, p=self.p
        )

        if (
            self.weights == "uniform"
            and self._fit_method == "brute"
            and not self.outputs_2d_
            and RadiusNeighborsClassMode.is_usable_for(X, self._fit_X, metric)
        ):
            probabilities = RadiusNeighborsClassMode.compute(
                X=X,
                Y=self._fit_X,
                radius=self.radius,
                weights=self.weights,
                Y_labels=self._y,
                unique_Y_labels=self.classes_,
                outlier_label=self.outlier_label,
                metric=metric,
                metric_kwargs=metric_kwargs,
                strategy="parallel_on_X",
                # `strategy="parallel_on_X"` has in practice be shown
                # to be more efficient than `strategy="parallel_on_Y``
                # on many combination of datasets.
                # Hence, we choose to enforce it here.
                # For more information, see:
                # https://github.com/scikit-learn/scikit-learn/pull/26828/files#r1282398471
            )
            return probabilities

        neigh_dist, neigh_ind = self.radius_neighbors(X)
        outlier_mask = np.zeros(n_queries, dtype=bool)
        outlier_mask[:] = [len(nind) == 0 for nind in neigh_ind]
        outliers = np.flatnonzero(outlier_mask)
        inliers = np.flatnonzero(~outlier_mask)

        classes_ = self.classes_
        _y = self._y
        if not self.outputs_2d_:
            _y = self._y.reshape((-1, 1))
            classes_ = [self.classes_]

        if self.outlier_label_ is None and outliers.size > 0:
            raise ValueError(
                "No neighbors found for test samples %r, "
                "you can try using larger radius, "
                "giving a label for outliers, "
                "or considering removing them from your dataset." % outliers
            )

        weights = _get_weights(neigh_dist, self.weights)
        if weights is not None:
            weights = weights[inliers]

        probabilities = []
        # iterate over multi-output, measure probabilities of the k-th output.
        for k, classes_k in enumerate(classes_):
            pred_labels = np.zeros(len(neigh_ind), dtype=object)
            pred_labels[:] = [_y[ind, k] for ind in neigh_ind]

            proba_k = np.zeros((n_queries, classes_k.size))
            proba_inl = np.zeros((len(inliers), classes_k.size))

            # samples have different size of neighbors within the same radius
            if weights is None:
                for i, idx in enumerate(pred_labels[inliers]):
                    proba_inl[i, :] = np.bincount(idx, minlength=classes_k.size)
            else:
                for i, idx in enumerate(pred_labels[inliers]):
                    proba_inl[i, :] = np.bincount(
                        idx, weights[i], minlength=classes_k.size
                    )
            proba_k[inliers, :] = proba_inl

            if outliers.size > 0:
                _outlier_label = self.outlier_label_[k]
                label_index = np.flatnonzero(classes_k == _outlier_label)
                if label_index.size == 1:
                    proba_k[outliers, label_index[0]] = 1.0
                else:
                    warnings.warn(
                        "Outlier label {} is not in training "
                        "classes. All class probabilities of "
                        "outliers will be assigned with 0."
                        "".format(self.outlier_label_[k])
                    )

            # normalize 'votes' into real [0,1] probabilities
            normalizer = proba_k.sum(axis=1)[:, np.newaxis]
            normalizer[normalizer == 0.0] = 1.0
            proba_k /= normalizer

            probabilities.append(proba_k)

        if not self.outputs_2d_:
            probabilities = probabilities[0]

        return probabilities