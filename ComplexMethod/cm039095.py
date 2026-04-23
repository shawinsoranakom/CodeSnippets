def inverse_transform(self, X):
        """
        Convert the data back to the original representation.

        When unknown categories are encountered (all zeros in the
        one-hot encoding), ``None`` is used to represent this category. If the
        feature with the unknown category has a dropped category, the dropped
        category will be its inverse.

        For a given input feature, if there is an infrequent category,
        'infrequent_sklearn' will be used to represent the infrequent category.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape \
                (n_samples, n_encoded_features)
            The transformed data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Inverse transformed array.
        """
        check_is_fitted(self)
        X = check_array(X, accept_sparse="csr")

        n_samples, _ = X.shape
        n_features = len(self.categories_)

        n_features_out = np.sum(self._n_features_outs)

        # validate shape of passed X
        msg = (
            "Shape of the passed X data is not correct. Expected {0} columns, got {1}."
        )
        if X.shape[1] != n_features_out:
            raise ValueError(msg.format(n_features_out, X.shape[1]))

        transformed_features = [
            self._compute_transformed_categories(i, remove_dropped=False)
            for i, _ in enumerate(self.categories_)
        ]

        # create resulting array of appropriate dtype
        dt = np.result_type(*[cat.dtype for cat in transformed_features])
        X_tr = np.empty((n_samples, n_features), dtype=dt)

        j = 0
        found_unknown = {}

        if self._infrequent_enabled:
            infrequent_indices = self._infrequent_indices
        else:
            infrequent_indices = [None] * n_features

        for i in range(n_features):
            cats_wo_dropped = self._remove_dropped_categories(
                transformed_features[i], i
            )
            n_categories = cats_wo_dropped.shape[0]

            # Only happens if there was a column with a unique
            # category. In this case we just fill the column with this
            # unique category value.
            if n_categories == 0:
                X_tr[:, i] = self.categories_[i][self._drop_idx_after_grouping[i]]
                j += n_categories
                continue
            sub = X[:, j : j + n_categories]
            # for sparse X argmax returns 2D matrix, ensure 1D array
            labels = np.asarray(sub.argmax(axis=1)).flatten()
            X_tr[:, i] = cats_wo_dropped[labels]

            if self.handle_unknown == "ignore" or (
                self.handle_unknown in ("infrequent_if_exist", "warn")
                and infrequent_indices[i] is None
            ):
                unknown = np.asarray(sub.sum(axis=1) == 0).flatten()
                # ignored unknown categories: we have a row of all zero
                if unknown.any():
                    # if categories were dropped then unknown categories will
                    # be mapped to the dropped category
                    if (
                        self._drop_idx_after_grouping is None
                        or self._drop_idx_after_grouping[i] is None
                    ):
                        found_unknown[i] = unknown
                    else:
                        X_tr[unknown, i] = self.categories_[i][
                            self._drop_idx_after_grouping[i]
                        ]
            else:
                dropped = np.asarray(sub.sum(axis=1) == 0).flatten()
                if dropped.any():
                    if self._drop_idx_after_grouping is None:
                        all_zero_samples = np.flatnonzero(dropped)
                        raise ValueError(
                            f"Samples {all_zero_samples} can not be inverted "
                            "when drop=None and handle_unknown='error' "
                            "because they contain all zeros"
                        )
                    # we can safely assume that all of the nulls in each column
                    # are the dropped value
                    drop_idx = self._drop_idx_after_grouping[i]
                    X_tr[dropped, i] = transformed_features[i][drop_idx]

            j += n_categories

        # if ignored are found: potentially need to upcast result to
        # insert None values
        if found_unknown:
            if X_tr.dtype != object:
                X_tr = X_tr.astype(object)

            for idx, mask in found_unknown.items():
                X_tr[mask, idx] = None

        return X_tr