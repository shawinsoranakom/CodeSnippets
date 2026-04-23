def inverse_transform(self, X):
        """
        Convert the data back to the original representation.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_encoded_features)
            The transformed data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Inverse transformed array.
        """
        check_is_fitted(self)
        X = check_array(X, ensure_all_finite="allow-nan")

        n_samples, _ = X.shape
        n_features = len(self.categories_)

        # validate shape of passed X
        msg = (
            "Shape of the passed X data is not correct. Expected {0} columns, got {1}."
        )
        if X.shape[1] != n_features:
            raise ValueError(msg.format(n_features, X.shape[1]))

        # create resulting array of appropriate dtype
        dt = np.result_type(*[cat.dtype for cat in self.categories_])
        X_tr = np.empty((n_samples, n_features), dtype=dt)

        found_unknown = {}
        infrequent_masks = {}

        infrequent_indices = getattr(self, "_infrequent_indices", None)

        for i in range(n_features):
            labels = X[:, i]

            # replace values of X[:, i] that were nan with actual indices
            if i in self._missing_indices:
                X_i_mask = _get_mask(labels, self.encoded_missing_value)
                labels[X_i_mask] = self._missing_indices[i]

            rows_to_update = slice(None)
            categories = self.categories_[i]

            if infrequent_indices is not None and infrequent_indices[i] is not None:
                # Compute mask for frequent categories
                infrequent_encoding_value = len(categories) - len(infrequent_indices[i])
                infrequent_masks[i] = labels == infrequent_encoding_value
                rows_to_update = ~infrequent_masks[i]

                # Remap categories to be only frequent categories. The infrequent
                # categories will be mapped to "infrequent_sklearn" later
                frequent_categories_mask = np.ones_like(categories, dtype=bool)
                frequent_categories_mask[infrequent_indices[i]] = False
                categories = categories[frequent_categories_mask]

            if self.handle_unknown == "use_encoded_value":
                unknown_labels = _get_mask(labels, self.unknown_value)
                found_unknown[i] = unknown_labels

                known_labels = ~unknown_labels
                if isinstance(rows_to_update, np.ndarray):
                    rows_to_update &= known_labels
                else:
                    rows_to_update = known_labels

            labels_int = labels[rows_to_update].astype("int64", copy=False)
            X_tr[rows_to_update, i] = categories[labels_int]

        if found_unknown or infrequent_masks:
            X_tr = X_tr.astype(object, copy=False)

        # insert None values for unknown values
        if found_unknown:
            for idx, mask in found_unknown.items():
                X_tr[mask, idx] = None

        if infrequent_masks:
            for idx, mask in infrequent_masks.items():
                X_tr[mask, idx] = "infrequent_sklearn"

        return X_tr