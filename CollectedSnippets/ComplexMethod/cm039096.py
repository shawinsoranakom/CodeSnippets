def fit(self, X, y=None):
        """
        Fit the OrdinalEncoder to X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to determine the categories of each feature.

        y : None
            Ignored. This parameter exists only for compatibility with
            :class:`~sklearn.pipeline.Pipeline`.

        Returns
        -------
        self : object
            Fitted encoder.
        """
        if self.handle_unknown == "use_encoded_value":
            if is_scalar_nan(self.unknown_value):
                if np.dtype(self.dtype).kind != "f":
                    raise ValueError(
                        "When unknown_value is np.nan, the dtype "
                        "parameter should be "
                        f"a float dtype. Got {self.dtype}."
                    )
            elif not isinstance(self.unknown_value, numbers.Integral):
                raise TypeError(
                    "unknown_value should be an integer or "
                    "np.nan when "
                    "handle_unknown is 'use_encoded_value', "
                    f"got {self.unknown_value}."
                )
        elif self.unknown_value is not None:
            raise TypeError(
                "unknown_value should only be set when "
                "handle_unknown is 'use_encoded_value', "
                f"got {self.unknown_value}."
            )

        # `_fit` will only raise an error when `self.handle_unknown="error"`
        fit_results = self._fit(
            X,
            handle_unknown=self.handle_unknown,
            ensure_all_finite="allow-nan",
            return_and_ignore_missing_for_infrequent=True,
        )
        self._missing_indices = fit_results["missing_indices"]

        cardinalities = [len(categories) for categories in self.categories_]
        if self._infrequent_enabled:
            # Cardinality decreases because the infrequent categories are grouped
            # together
            for feature_idx, infrequent in enumerate(self.infrequent_categories_):
                if infrequent is not None:
                    cardinalities[feature_idx] -= len(infrequent)

        # missing values are not considered part of the cardinality
        # when considering unknown categories or encoded_missing_value
        for cat_idx, categories_for_idx in enumerate(self.categories_):
            if is_scalar_nan(categories_for_idx[-1]):
                cardinalities[cat_idx] -= 1

        if self.handle_unknown == "use_encoded_value":
            for cardinality in cardinalities:
                if 0 <= self.unknown_value < cardinality:
                    raise ValueError(
                        "The used value for unknown_value "
                        f"{self.unknown_value} is one of the "
                        "values already used for encoding the "
                        "seen categories."
                    )

        if self._missing_indices:
            if np.dtype(self.dtype).kind != "f" and is_scalar_nan(
                self.encoded_missing_value
            ):
                raise ValueError(
                    "There are missing values in features "
                    f"{list(self._missing_indices)}. For OrdinalEncoder to "
                    f"encode missing values with dtype: {self.dtype}, set "
                    "encoded_missing_value to a non-nan value, or "
                    "set dtype to a float"
                )

            if not is_scalar_nan(self.encoded_missing_value):
                # Features are invalid when they contain a missing category
                # and encoded_missing_value was already used to encode a
                # known category
                invalid_features = [
                    cat_idx
                    for cat_idx, cardinality in enumerate(cardinalities)
                    if cat_idx in self._missing_indices
                    and 0 <= self.encoded_missing_value < cardinality
                ]

                if invalid_features:
                    # Use feature names if they are available
                    if hasattr(self, "feature_names_in_"):
                        invalid_features = self.feature_names_in_[invalid_features]
                    raise ValueError(
                        f"encoded_missing_value ({self.encoded_missing_value}) "
                        "is already used to encode a known category in features: "
                        f"{invalid_features}"
                    )

        return self