def _transform(
        self,
        X,
        handle_unknown="error",
        ensure_all_finite=True,
        warn_on_unknown=False,
        ignore_category_indices=None,
    ):
        X_list, n_samples, n_features = self._check_X(
            X, ensure_all_finite=ensure_all_finite
        )
        validate_data(self, X=X, reset=False, skip_check_array=True)

        X_int = np.zeros((n_samples, n_features), dtype=int)
        X_mask = np.ones((n_samples, n_features), dtype=bool)

        columns_with_unknown = []
        for i in range(n_features):
            Xi = X_list[i]
            diff, valid_mask = _check_unknown(Xi, self.categories_[i], return_mask=True)

            if not np.all(valid_mask):
                if handle_unknown == "error":
                    msg = (
                        "Found unknown categories {0} in column {1}"
                        " during transform".format(diff, i)
                    )
                    raise ValueError(msg)
                else:
                    if warn_on_unknown:
                        columns_with_unknown.append(i)
                    # Set the problematic rows to an acceptable value and
                    # continue `The rows are marked `X_mask` and will be
                    # removed later.
                    X_mask[:, i] = valid_mask
                    # cast Xi into the largest string type necessary
                    # to handle different lengths of numpy strings
                    if (
                        self.categories_[i].dtype.kind in ("U", "S")
                        and self.categories_[i].itemsize > Xi.itemsize
                    ):
                        Xi = Xi.astype(self.categories_[i].dtype)
                    elif self.categories_[i].dtype.kind == "O" and Xi.dtype.kind == "U":
                        # categories are objects and Xi are numpy strings.
                        # Cast Xi to an object dtype to prevent truncation
                        # when setting invalid values.
                        Xi = Xi.astype("O")
                    else:
                        Xi = Xi.copy()

                    Xi[~valid_mask] = self.categories_[i][0]
            # We use check_unknown=False, since _check_unknown was
            # already called above.
            X_int[:, i] = _encode(Xi, uniques=self.categories_[i], check_unknown=False)
        if columns_with_unknown:
            if handle_unknown == "infrequent_if_exist":
                msg = (
                    "Found unknown categories in columns "
                    f"{columns_with_unknown} during transform. These "
                    "unknown categories will be encoded as the "
                    "infrequent category."
                )
            else:
                msg = (
                    "Found unknown categories in columns "
                    f"{columns_with_unknown} during transform. These "
                    "unknown categories will be encoded as all zeros"
                )
            warnings.warn(msg, UserWarning)

        self._map_infrequent_categories(X_int, X_mask, ignore_category_indices)
        return X_int, X_mask