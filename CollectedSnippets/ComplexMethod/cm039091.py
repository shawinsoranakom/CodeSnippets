def _map_infrequent_categories(self, X_int, X_mask, ignore_category_indices):
        """Map infrequent categories to integer representing the infrequent category.

        This modifies X_int in-place. Values that were invalid based on `X_mask`
        are mapped to the infrequent category if there was an infrequent
        category for that feature.

        Parameters
        ----------
        X_int: ndarray of shape (n_samples, n_features)
            Integer encoded categories.

        X_mask: ndarray of shape (n_samples, n_features)
            Bool mask for valid values in `X_int`.

        ignore_category_indices : dict
            Dictionary mapping from feature_idx to category index to ignore.
            Ignored indexes will not be grouped and the original ordinal encoding
            will remain.
        """
        if not self._infrequent_enabled:
            return

        ignore_category_indices = ignore_category_indices or {}

        for col_idx in range(X_int.shape[1]):
            infrequent_idx = self._infrequent_indices[col_idx]
            if infrequent_idx is None:
                continue

            X_int[~X_mask[:, col_idx], col_idx] = infrequent_idx[0]
            if self.handle_unknown in ("infrequent_if_exist", "warn"):
                # All the unknown values are now mapped to the
                # infrequent_idx[0], which makes the unknown values valid
                # This is needed in `transform` when the encoding is formed
                # using `X_mask`.
                X_mask[:, col_idx] = True

        # Remaps encoding in `X_int` where the infrequent categories are
        # grouped together.
        for i, mapping in enumerate(self._default_to_infrequent_mappings):
            if mapping is None:
                continue

            if i in ignore_category_indices:
                # Update rows that are **not** ignored
                rows_to_update = X_int[:, i] != ignore_category_indices[i]
            else:
                rows_to_update = slice(None)

            X_int[rows_to_update, i] = np.take(mapping, X_int[rows_to_update, i])