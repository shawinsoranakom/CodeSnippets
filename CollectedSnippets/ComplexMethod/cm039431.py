def _check_categorical_features(self, X):
        """Check and validate categorical features in X

        Parameters
        ----------
        X : {array-like, pandas DataFrame} of shape (n_samples, n_features)
            Input data.

        Return
        ------
        is_categorical : ndarray of shape (n_features,) or None, dtype=bool
            Indicates whether a feature is categorical. If no feature is
            categorical, this is None.
        """
        # Special code for pandas because of a bug in recent pandas, which is
        # fixed in main and maybe included in 2.2.1, see
        # https://github.com/pandas-dev/pandas/pull/57173.
        # Also pandas versions < 1.5.1 do not support the dataframe interchange
        if is_pandas_df(X):
            X_is_dataframe = True
            categorical_columns_mask = np.asarray(X.dtypes == "category")
        elif hasattr(X, "__dataframe__"):
            X_is_dataframe = True
            categorical_columns_mask = np.asarray(
                [
                    c.dtype[0].name == "CATEGORICAL"
                    for c in X.__dataframe__().get_columns()
                ]
            )
        else:
            X_is_dataframe = False
            categorical_columns_mask = None

        categorical_features = self.categorical_features

        categorical_by_dtype = (
            isinstance(categorical_features, str)
            and categorical_features == "from_dtype"
        )
        no_categorical_dtype = categorical_features is None or (
            categorical_by_dtype and not X_is_dataframe
        )

        if no_categorical_dtype:
            return None

        use_pandas_categorical = categorical_by_dtype and X_is_dataframe
        if use_pandas_categorical:
            categorical_features = categorical_columns_mask
        else:
            categorical_features = np.asarray(categorical_features)

        if categorical_features.size == 0:
            return None

        if categorical_features.dtype.kind not in ("i", "b", "U", "O"):
            raise ValueError(
                "categorical_features must be an array-like of bool, int or "
                f"str, got: {categorical_features.dtype.name}."
            )

        if categorical_features.dtype.kind == "O":
            types = set(type(f) for f in categorical_features)
            if types != {str}:
                raise ValueError(
                    "categorical_features must be an array-like of bool, int or "
                    f"str, got: {', '.join(sorted(t.__name__ for t in types))}."
                )

        n_features = X.shape[1]
        # At this point `validate_data` was not called yet because we use the original
        # dtypes to discover the categorical features. Thus `feature_names_in_`
        # is not defined yet.
        feature_names_in_ = getattr(X, "columns", None)

        if categorical_features.dtype.kind in ("U", "O"):
            # check for feature names
            if feature_names_in_ is None:
                raise ValueError(
                    "categorical_features should be passed as an array of "
                    "integers or as a boolean mask when the model is fitted "
                    "on data without feature names."
                )
            is_categorical = np.zeros(n_features, dtype=bool)
            feature_names = list(feature_names_in_)
            for feature_name in categorical_features:
                try:
                    is_categorical[feature_names.index(feature_name)] = True
                except ValueError as e:
                    raise ValueError(
                        f"categorical_features has an item value '{feature_name}' "
                        "which is not a valid feature name of the training "
                        f"data. Observed feature names: {feature_names}"
                    ) from e
        elif categorical_features.dtype.kind == "i":
            # check for categorical features as indices
            if (
                np.max(categorical_features) >= n_features
                or np.min(categorical_features) < 0
            ):
                raise ValueError(
                    "categorical_features set as integer "
                    "indices must be in [0, n_features - 1]"
                )
            is_categorical = np.zeros(n_features, dtype=bool)
            is_categorical[categorical_features] = True
        else:
            if categorical_features.shape[0] != n_features:
                raise ValueError(
                    "categorical_features set as a boolean mask "
                    "must have shape (n_features,), got: "
                    f"{categorical_features.shape}"
                )
            is_categorical = categorical_features

        if not np.any(is_categorical):
            return None
        return is_categorical