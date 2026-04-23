def fit_transform(self, X, y=None, **params):
        """Fit all transformers, transform the data and concatenate results.

        Parameters
        ----------
        X : {array-like, dataframe} of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the
            transformers.

        y : array-like of shape (n_samples,), default=None
            Targets for supervised learning.

        **params : dict, default=None
            Parameters to be passed to the underlying transformers' ``fit`` and
            ``transform`` methods.

            You can only pass this if metadata routing is enabled, which you
            can enable using ``sklearn.set_config(enable_metadata_routing=True)``.

            .. versionadded:: 1.4

        Returns
        -------
        X_t : {array-like, sparse matrix} of \
                shape (n_samples, sum_n_components)
            Horizontally stacked results of transformers. sum_n_components is the
            sum of n_components (output dimension) over transformers. If
            any result is a sparse matrix, everything will be converted to
            sparse matrices.
        """
        _raise_for_params(params, self, "fit_transform")

        validate_data(self, X=X, skip_check_array=True)
        X = _check_X(X)
        # set n_features_in_ attribute
        self._validate_transformers()
        n_samples = _num_samples(X)

        self._validate_column_callables(X)
        self._validate_remainder(X)

        if _routing_enabled():
            routed_params = process_routing(self, "fit_transform", **params)
        else:
            routed_params = self._get_empty_routing()

        result = self._call_func_on_transformers(
            X,
            y,
            _fit_transform_one,
            column_as_labels=False,
            routed_params=routed_params,
        )

        if not result:
            self._update_fitted_transformers([])
            # All transformers are None
            return np.zeros((n_samples, 0))

        Xs, transformers = zip(*result)

        # determine if concatenated output will be sparse or not
        if any(sparse.issparse(X) for X in Xs):
            nnz = sum(
                X.nnz if sparse.issparse(X) else X.shape[0] * X.shape[1] for X in Xs
            )
            total = sum(X.shape[0] * X.shape[1] for X in Xs)
            density = nnz / total
            self.sparse_output_ = density < self.sparse_threshold
        else:
            self.sparse_output_ = False

        self._update_fitted_transformers(transformers)
        self._validate_output(Xs)
        self._record_output_indices(Xs)

        return self._hstack(list(Xs), n_samples=n_samples)