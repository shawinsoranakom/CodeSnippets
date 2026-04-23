def predict(self, X):
        """Predict the target for the provided data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_queries, n_features), \
                or (n_queries, n_indexed) if metric == 'precomputed', or None
            Test samples. If `None`, predictions for all indexed points are
            returned; in this case, points are not considered their own
            neighbors.

        Returns
        -------
        y : ndarray of shape (n_queries,) or (n_queries, n_outputs), \
                dtype=double
            Target values.
        """
        neigh_dist, neigh_ind = self.radius_neighbors(X)

        weights = _get_weights(neigh_dist, self.weights)

        _y = self._y
        if _y.ndim == 1:
            _y = _y.reshape((-1, 1))

        empty_obs = np.full_like(_y[0], np.nan)

        if weights is None:
            y_pred = np.array(
                [
                    np.mean(_y[ind, :], axis=0) if len(ind) else empty_obs
                    for (i, ind) in enumerate(neigh_ind)
                ]
            )

        else:
            y_pred = np.array(
                [
                    (
                        np.average(_y[ind, :], axis=0, weights=weights[i])
                        if len(ind)
                        else empty_obs
                    )
                    for (i, ind) in enumerate(neigh_ind)
                ]
            )

        if np.any(np.isnan(y_pred)):
            empty_warning_msg = (
                "One or more samples have no neighbors "
                "within specified radius; predicting NaN."
            )
            warnings.warn(empty_warning_msg)

        if self._y.ndim == 1:
            y_pred = y_pred.ravel()

        return y_pred