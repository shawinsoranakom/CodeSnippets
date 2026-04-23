def transform(self, X):
        """
        Transform X using one-hot encoding.

        If `sparse_output=True` (default), it returns a SciPy sparse in CSR format.

        If there are infrequent categories for a feature, set by specifying
        `max_categories` or `min_frequency`, the infrequent categories are
        grouped into a single category.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to encode.

        Returns
        -------
        X_out : {ndarray, sparse matrix} of shape \
                (n_samples, n_encoded_features)
            Transformed input. If `sparse_output=True`, a sparse matrix will be
            returned.
        """
        check_is_fitted(self)
        transform_output = _get_output_config("transform", estimator=self)["dense"]
        if transform_output != "default" and self.sparse_output:
            capitalize_transform_output = transform_output.capitalize()
            raise ValueError(
                f"{capitalize_transform_output} output does not support sparse data."
                f" Set sparse_output=False to output {transform_output} dataframes or"
                f" disable {capitalize_transform_output} output via"
                '` ohe.set_output(transform="default").'
            )

        # validation of X happens in _check_X called by _transform
        if self.handle_unknown == "warn":
            warn_on_unknown, handle_unknown = True, "infrequent_if_exist"
        else:
            warn_on_unknown = self.drop is not None and self.handle_unknown in {
                "ignore",
                "infrequent_if_exist",
            }
            handle_unknown = self.handle_unknown
        X_int, X_mask = self._transform(
            X,
            handle_unknown=handle_unknown,
            ensure_all_finite="allow-nan",
            warn_on_unknown=warn_on_unknown,
        )

        n_samples, n_features = X_int.shape

        if self._drop_idx_after_grouping is not None:
            to_drop = self._drop_idx_after_grouping.copy()
            # We remove all the dropped categories from mask, and decrement all
            # categories that occur after them to avoid an empty column.
            keep_cells = X_int != to_drop
            for i, cats in enumerate(self.categories_):
                # drop='if_binary' but feature isn't binary
                if to_drop[i] is None:
                    # set to cardinality to not drop from X_int
                    to_drop[i] = len(cats)

            to_drop = to_drop.reshape(1, -1)
            X_int[X_int > to_drop] -= 1
            X_mask &= keep_cells

        mask = X_mask.ravel()
        feature_indices = np.cumsum([0] + self._n_features_outs)
        indices = (X_int + feature_indices[:-1]).ravel()[mask]

        indptr = np.empty(n_samples + 1, dtype=int)
        indptr[0] = 0
        np.sum(X_mask, axis=1, out=indptr[1:], dtype=indptr.dtype)
        np.cumsum(indptr[1:], out=indptr[1:])
        data = np.ones(indptr[-1])

        out = sparse.csr_array(
            (data, indices, indptr),
            shape=(n_samples, feature_indices[-1]),
            dtype=self.dtype,
        )
        if self.sparse_output:
            _ensure_sparse_index_int32(out)
            return _align_api_if_sparse(out)
        else:
            return out.toarray()