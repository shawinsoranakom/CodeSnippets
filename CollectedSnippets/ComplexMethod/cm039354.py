def _validate_limit(
        limit, limit_type, n_features, is_empty_feature, keep_empty_feature
    ):
        """Validate the limits (min/max) of the feature values.

        Converts scalar min/max limits to vectors of shape `(n_features,)`.

        Parameters
        ----------
        limit: scalar or array-like
            The user-specified limit (i.e, min_value or max_value).
        limit_type: {'max', 'min'}
            Type of limit to validate.
        n_features: int
            Number of features in the dataset.
        is_empty_feature: ndarray, shape (n_features, )
            Mask array indicating empty feature imputer has seen during fit.
        keep_empty_feature: bool
            If False, remove empty-feature indices from the limit.

        Returns
        -------
        limit: ndarray, shape(n_features,)
            Array of limits, one for each feature.
        """
        n_features_in = _num_samples(is_empty_feature)
        if (
            limit is not None
            and not np.isscalar(limit)
            and _num_samples(limit) != n_features_in
        ):
            raise ValueError(
                f"'{limit_type}_value' should be of shape ({n_features_in},) when an"
                f" array-like is provided. Got {len(limit)}, instead."
            )

        limit_bound = np.inf if limit_type == "max" else -np.inf
        limit = limit_bound if limit is None else limit
        if np.isscalar(limit):
            limit = np.full(n_features, limit)
        limit = check_array(limit, ensure_all_finite=False, copy=False, ensure_2d=False)

        # Make sure to remove the empty feature elements from the bounds
        if not keep_empty_feature and len(limit) == len(is_empty_feature):
            limit = limit[~is_empty_feature]

        return limit