def _fit(
        self,
        X,
        handle_unknown="error",
        ensure_all_finite=True,
        return_counts=False,
        return_and_ignore_missing_for_infrequent=False,
    ):
        self._check_infrequent_enabled()
        validate_data(self, X=X, reset=True, skip_check_array=True)
        X_list, n_samples, n_features = self._check_X(
            X, ensure_all_finite=ensure_all_finite
        )
        self.n_features_in_ = n_features

        if self.categories != "auto":
            if len(self.categories) != n_features:
                raise ValueError(
                    "Shape mismatch: if categories is an array,"
                    " it has to be of shape (n_features,)."
                )

        self.categories_ = []
        category_counts = []
        compute_counts = return_counts or self._infrequent_enabled

        for i in range(n_features):
            Xi = X_list[i]

            if self.categories == "auto":
                result = _unique(Xi, return_counts=compute_counts)
                if compute_counts:
                    cats, counts = result
                    category_counts.append(counts)
                else:
                    cats = result
            else:
                if np.issubdtype(Xi.dtype, np.str_):
                    # Always convert string categories to objects to avoid
                    # unexpected string truncation for longer category labels
                    # passed in the constructor.
                    Xi_dtype = object
                else:
                    Xi_dtype = Xi.dtype

                cats = np.array(self.categories[i], dtype=Xi_dtype)
                if (
                    cats.dtype == object
                    and isinstance(cats[0], bytes)
                    and Xi.dtype.kind != "S"
                ):
                    msg = (
                        f"In column {i}, the predefined categories have type 'bytes'"
                        " which is incompatible with values of type"
                        f" '{type(Xi[0]).__name__}'."
                    )
                    raise ValueError(msg)

                # `nan` must be the last stated category
                for category in cats[:-1]:
                    if is_scalar_nan(category):
                        raise ValueError(
                            "Nan should be the last element in user"
                            f" provided categories, see categories {cats}"
                            f" in column #{i}"
                        )

                if cats.size != len(_unique(cats)):
                    msg = (
                        f"In column {i}, the predefined categories"
                        " contain duplicate elements."
                    )
                    raise ValueError(msg)

                if Xi.dtype.kind not in "OUS":
                    sorted_cats = np.sort(cats)
                    error_msg = (
                        "Unsorted categories are not supported for numerical categories"
                    )
                    # if there are nans, nan should be the last element
                    stop_idx = -1 if np.isnan(sorted_cats[-1]) else None
                    if np.any(sorted_cats[:stop_idx] != cats[:stop_idx]):
                        raise ValueError(error_msg)

                if handle_unknown == "error":
                    diff = _check_unknown(Xi, cats)
                    if diff:
                        msg = (
                            "Found unknown categories {0} in column {1}"
                            " during fit".format(diff, i)
                        )
                        raise ValueError(msg)
                if compute_counts:
                    category_counts.append(_get_counts(Xi, cats))

            self.categories_.append(cats)

        output = {"n_samples": n_samples}
        if return_counts:
            output["category_counts"] = category_counts

        missing_indices = {}
        if return_and_ignore_missing_for_infrequent:
            for feature_idx, categories_for_idx in enumerate(self.categories_):
                if is_scalar_nan(categories_for_idx[-1]):
                    # `nan` values can only be placed in the latest position
                    missing_indices[feature_idx] = categories_for_idx.size - 1
            output["missing_indices"] = missing_indices

        if self._infrequent_enabled:
            self._fit_infrequent_category_mapping(
                n_samples,
                category_counts,
                missing_indices,
            )
        return output