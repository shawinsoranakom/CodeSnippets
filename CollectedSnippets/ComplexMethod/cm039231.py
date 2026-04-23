def transform(self, X, **params):
        """Transform X separately by each transformer, concatenate results.

        Parameters
        ----------
        X : {array-like, dataframe} of shape (n_samples, n_features)
            The data to be transformed by subset.

        **params : dict, default=None
            Parameters to be passed to the underlying transformers' ``transform``
            method.

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
        _raise_for_params(params, self, "transform")
        check_is_fitted(self)
        X = _check_X(X)

        # If ColumnTransformer is fit using a dataframe, and now a dataframe is
        # passed to be transformed, we select columns by name instead. This
        # enables the user to pass X at transform time with extra columns which
        # were not present in fit time, and the order of the columns doesn't
        # matter.
        fit_dataframe_and_transform_dataframe = hasattr(self, "feature_names_in_") and (
            is_pandas_df(X) or hasattr(X, "__dataframe__")
        )

        n_samples = _num_samples(X)
        column_names = _get_feature_names(X)

        if fit_dataframe_and_transform_dataframe:
            named_transformers = self.named_transformers_
            # check that all names seen in fit are in transform, unless
            # they were dropped
            non_dropped_indices = [
                ind
                for name, ind in self._transformer_to_input_indices.items()
                if name in named_transformers and named_transformers[name] != "drop"
            ]

            all_indices = set(chain(*non_dropped_indices))
            all_names = set(self.feature_names_in_[ind] for ind in all_indices)

            diff = all_names - set(column_names)
            if diff:
                raise ValueError(f"columns are missing: {diff}")
        else:
            # ndarray was used for fitting or transforming, thus we only
            # check that n_features_in_ is consistent
            _check_n_features(self, X, reset=False)

        if _routing_enabled():
            routed_params = process_routing(self, "transform", **params)
        else:
            routed_params = self._get_empty_routing()

        Xs = self._call_func_on_transformers(
            X,
            None,
            _transform_one,
            column_as_labels=fit_dataframe_and_transform_dataframe,
            routed_params=routed_params,
        )
        self._validate_output(Xs)

        if not Xs:
            # All transformers are None
            return np.zeros((n_samples, 0))

        return self._hstack(list(Xs), n_samples=n_samples)