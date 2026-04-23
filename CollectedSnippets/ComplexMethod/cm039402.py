def radius_neighbors(
        self, X=None, radius=None, return_distance=True, sort_results=False
    ):
        """Find the neighbors within a given radius of a point or points.

        Return the indices and distances of each point from the dataset
        lying in a ball with size ``radius`` around the points of the query
        array. Points lying on the boundary are included in the results.

        The result points are *not* necessarily sorted by distance to their
        query point.

        Parameters
        ----------
        X : {array-like, sparse matrix} of (n_samples, n_features), default=None
            The query point or points.
            If not provided, neighbors of each indexed point are returned.
            In this case, the query point is not considered its own neighbor.

        radius : float, default=None
            Limiting distance of neighbors to return. The default is the value
            passed to the constructor.

        return_distance : bool, default=True
            Whether or not to return the distances.

        sort_results : bool, default=False
            If True, the distances and indices will be sorted by increasing
            distances before being returned. If False, the results may not
            be sorted. If `return_distance=False`, setting `sort_results=True`
            will result in an error.

            .. versionadded:: 0.22

        Returns
        -------
        neigh_dist : ndarray of shape (n_samples,) of arrays
            Array representing the distances to each point, only present if
            `return_distance=True`. The distance values are computed according
            to the ``metric`` constructor parameter.

        neigh_ind : ndarray of shape (n_samples,) of arrays
            An array of arrays of indices of the approximate nearest points
            from the population matrix that lie within a ball of size
            ``radius`` around the query points.

        Notes
        -----
        Because the number of neighbors of each point is not necessarily
        equal, the results for multiple query points cannot be fit in a
        standard data array.
        For efficiency, `radius_neighbors` returns arrays of objects, where
        each object is a 1D array of indices or distances.

        Examples
        --------
        In the following example, we construct a NeighborsClassifier
        class from an array representing our data set and ask who's
        the closest point to [1, 1, 1]:

        >>> import numpy as np
        >>> samples = [[0., 0., 0.], [0., .5, 0.], [1., 1., .5]]
        >>> from sklearn.neighbors import NearestNeighbors
        >>> neigh = NearestNeighbors(radius=1.6)
        >>> neigh.fit(samples)
        NearestNeighbors(radius=1.6)
        >>> rng = neigh.radius_neighbors([[1., 1., 1.]])
        >>> print(np.asarray(rng[0][0]))
        [1.5 0.5]
        >>> print(np.asarray(rng[1][0]))
        [1 2]

        The first array returned contains the distances to all points which
        are closer than 1.6, while the second array returned contains their
        indices.  In general, multiple points can be queried at the same time.
        """
        check_is_fitted(self)

        if sort_results and not return_distance:
            raise ValueError("return_distance must be True if sort_results is True.")

        ensure_all_finite = "allow-nan" if get_tags(self).input_tags.allow_nan else True
        query_is_train = X is None
        if query_is_train:
            X = self._fit_X
        else:
            if self.metric == "precomputed":
                X = _check_precomputed(X)
            else:
                X = validate_data(
                    self,
                    X,
                    ensure_all_finite=ensure_all_finite,
                    accept_sparse="csr",
                    reset=False,
                    order="C",
                )

        if radius is None:
            radius = self.radius

        use_pairwise_distances_reductions = (
            self._fit_method == "brute"
            and RadiusNeighbors.is_usable_for(
                X if X is not None else self._fit_X, self._fit_X, self.effective_metric_
            )
        )

        if use_pairwise_distances_reductions:
            results = RadiusNeighbors.compute(
                X=X,
                Y=self._fit_X,
                radius=radius,
                metric=self.effective_metric_,
                metric_kwargs=self.effective_metric_params_,
                strategy="auto",
                return_distance=return_distance,
                sort_results=sort_results,
            )

        elif (
            self._fit_method == "brute" and self.metric == "precomputed" and issparse(X)
        ):
            results = _radius_neighbors_from_graph(
                X, radius=radius, return_distance=return_distance
            )

        elif self._fit_method == "brute":
            # Joblib-based backend, which is used when user-defined callable
            # are passed for metric.

            # This won't be used in the future once PairwiseDistancesReductions
            # support:
            #   - DistanceMetrics which work on supposedly binary data
            #   - CSR-dense and dense-CSR case if 'euclidean' in metric.

            # for efficiency, use squared euclidean distances
            if self.effective_metric_ == "euclidean":
                radius *= radius
                kwds = {"squared": True}
            else:
                kwds = self.effective_metric_params_

            reduce_func = partial(
                self._radius_neighbors_reduce_func,
                radius=radius,
                return_distance=return_distance,
            )

            chunked_results = pairwise_distances_chunked(
                X,
                self._fit_X,
                reduce_func=reduce_func,
                metric=self.effective_metric_,
                n_jobs=self.n_jobs,
                **kwds,
            )
            if return_distance:
                neigh_dist_chunks, neigh_ind_chunks = zip(*chunked_results)
                neigh_dist_list = list(itertools.chain.from_iterable(neigh_dist_chunks))
                neigh_ind_list = list(itertools.chain.from_iterable(neigh_ind_chunks))
                neigh_dist = _to_object_array(neigh_dist_list)
                neigh_ind = _to_object_array(neigh_ind_list)
                results = neigh_dist, neigh_ind
            else:
                neigh_ind_list = list(itertools.chain.from_iterable(chunked_results))
                results = _to_object_array(neigh_ind_list)

            if sort_results:
                for ii in range(len(neigh_dist)):
                    order = np.argsort(neigh_dist[ii], kind="mergesort")
                    neigh_ind[ii] = neigh_ind[ii][order]
                    neigh_dist[ii] = neigh_dist[ii][order]
                results = neigh_dist, neigh_ind

        elif self._fit_method in ["ball_tree", "kd_tree"]:
            if issparse(X):
                raise ValueError(
                    "%s does not work with sparse matrices. Densify the data, "
                    "or set algorithm='brute'" % self._fit_method
                )

            n_jobs = effective_n_jobs(self.n_jobs)
            delayed_query = delayed(self._tree.query_radius)
            chunked_results = Parallel(n_jobs, prefer="threads")(
                delayed_query(X[s], radius, return_distance, sort_results=sort_results)
                for s in gen_even_slices(X.shape[0], n_jobs)
            )
            if return_distance:
                neigh_ind, neigh_dist = tuple(zip(*chunked_results))
                results = np.hstack(neigh_dist), np.hstack(neigh_ind)
            else:
                results = np.hstack(chunked_results)
        else:
            raise ValueError("internal: _fit_method not recognized")

        if not query_is_train:
            return results
        else:
            # If the query data is the same as the indexed data, we would like
            # to ignore the first nearest neighbor of every sample, i.e
            # the sample itself.
            if return_distance:
                neigh_dist, neigh_ind = results
            else:
                neigh_ind = results

            for ind, ind_neighbor in enumerate(neigh_ind):
                mask = ind_neighbor != ind

                neigh_ind[ind] = ind_neighbor[mask]
                if return_distance:
                    neigh_dist[ind] = neigh_dist[ind][mask]

            if return_distance:
                return neigh_dist, neigh_ind
            return neigh_ind