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
        p : ndarray of shape (n_queries, n_classes), or a list of n_outputs \
                of such arrays if n_outputs > 1.
            The class probabilities of the input samples. Classes are ordered
            by lexicographic order.
        """
        check_is_fitted(self, "_fit_method")
        if self.weights == "uniform":
            # TODO: systematize this mapping of metric for
            # PairwiseDistancesReductions.
            metric, metric_kwargs = _adjusted_metric(
                metric=self.metric, metric_kwargs=self.metric_params, p=self.p
            )
            if (
                self._fit_method == "brute"
                and ArgKminClassMode.is_usable_for(X, self._fit_X, metric)
                # TODO: Implement efficient multi-output solution
                and not self.outputs_2d_
            ):
                if self.metric == "precomputed":
                    X = _check_precomputed(X)
                else:
                    X = validate_data(
                        self, X, accept_sparse="csr", reset=False, order="C"
                    )

                probabilities = ArgKminClassMode.compute(
                    X,
                    self._fit_X,
                    k=self.n_neighbors,
                    weights=self.weights,
                    Y_labels=self._y,
                    unique_Y_labels=self.classes_,
                    metric=metric,
                    metric_kwargs=metric_kwargs,
                    # `strategy="parallel_on_X"` has in practice be shown
                    # to be more efficient than `strategy="parallel_on_Y``
                    # on many combination of datasets.
                    # Hence, we choose to enforce it here.
                    # For more information, see:
                    # https://github.com/scikit-learn/scikit-learn/pull/24076#issuecomment-1445258342
                    # TODO: adapt the heuristic for `strategy="auto"` for
                    # `ArgKminClassMode` and use `strategy="auto"`.
                    strategy="parallel_on_X",
                )
                return probabilities

            # In that case, we do not need the distances to perform
            # the weighting so we do not compute them.
            neigh_ind = self.kneighbors(X, return_distance=False)
            neigh_dist = None
        else:
            neigh_dist, neigh_ind = self.kneighbors(X)

        classes_ = self.classes_
        _y = self._y
        if not self.outputs_2d_:
            _y = self._y.reshape((-1, 1))
            classes_ = [self.classes_]

        n_queries = _num_samples(self._fit_X if X is None else X)

        weights = _get_weights(neigh_dist, self.weights)
        if weights is None:
            weights = np.ones_like(neigh_ind)
        elif _all_with_any_reduction_axis_1(weights, value=0):
            raise ValueError(
                "All neighbors of some sample is getting zero weights. "
                "Please modify 'weights' to avoid this case if you are "
                "using a user-defined function."
            )

        all_rows = np.arange(n_queries)
        probabilities = []
        for k, classes_k in enumerate(classes_):
            pred_labels = _y[:, k][neigh_ind]
            proba_k = np.zeros((n_queries, classes_k.size))

            # a simple ':' index doesn't work right
            for i, idx in enumerate(pred_labels.T):  # loop is O(n_neighbors)
                proba_k[all_rows, idx] += weights[:, i]

            # normalize 'votes' into real [0,1] probabilities
            normalizer = proba_k.sum(axis=1)[:, np.newaxis]
            proba_k /= normalizer

            probabilities.append(proba_k)

        if not self.outputs_2d_:
            probabilities = probabilities[0]

        return probabilities