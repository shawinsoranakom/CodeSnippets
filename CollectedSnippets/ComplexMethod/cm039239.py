def _grid_from_X(X, percentiles, is_categorical, grid_resolution, custom_values):
    """Generate a grid of points based on the percentiles of X.

    The grid is a cartesian product between the columns of ``values``. The
    ith column of ``values`` consists in ``grid_resolution`` equally-spaced
    points between the percentiles of the jth column of X.

    If ``grid_resolution`` is bigger than the number of unique values in the
    j-th column of X or if the feature is a categorical feature (by inspecting
    `is_categorical`) , then those unique values will be used instead.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_target_features)
        The data.

    percentiles : tuple of float
        The percentiles which are used to construct the extreme values of
        the grid. Must be in [0, 1].

    is_categorical : list of bool
        For each feature, tells whether it is categorical or not. If a feature
        is categorical, then the values used will be the unique ones
        (i.e. categories) instead of the percentiles.

    grid_resolution : int
        The number of equally spaced points to be placed on the grid for each
        feature.

    custom_values: dict
        Mapping from column index of X to an array-like of values where
        the partial dependence should be calculated for that feature

    Returns
    -------
    grid : ndarray of shape (n_points, n_target_features)
        A value for each feature at each point in the grid. ``n_points`` is
        always ``<= grid_resolution ** X.shape[1]``.

    values : list of 1d ndarrays
        The values with which the grid has been created. The size of each
        array ``values[j]`` is either ``grid_resolution``, the number of
        unique values in ``X[:, j]``, if j is not in ``custom_range``.
        If j is in ``custom_range``, then it is the length of ``custom_range[j]``.
    """
    if not isinstance(percentiles, Iterable) or len(percentiles) != 2:
        raise ValueError("'percentiles' must be a sequence of 2 elements.")
    if not all(0 <= x <= 1 for x in percentiles):
        raise ValueError("'percentiles' values must be in [0, 1].")
    if percentiles[0] >= percentiles[1]:
        raise ValueError("percentiles[0] must be strictly less than percentiles[1].")

    if grid_resolution <= 1:
        raise ValueError("'grid_resolution' must be strictly greater than 1.")

    def _convert_custom_values(values):
        # Convert custom types such that object types are always used for string arrays
        dtype = object if any(isinstance(v, str) for v in values) else None
        return np.asarray(values, dtype=dtype)

    custom_values = {k: _convert_custom_values(v) for k, v in custom_values.items()}
    if any(v.ndim != 1 for v in custom_values.values()):
        error_string = ", ".join(
            f"Feature {k}: {v.ndim} dimensions"
            for k, v in custom_values.items()
            if v.ndim != 1
        )

        raise ValueError(
            "The custom grid for some features is not a one-dimensional array. "
            f"{error_string}"
        )

    values = []
    # TODO: we should handle missing values (i.e. `np.nan`) specifically and store them
    # in a different Bunch attribute.
    for feature, is_cat in enumerate(is_categorical):
        if feature in custom_values:
            # Use values in the custom range
            axis = custom_values[feature]
        else:
            try:
                uniques = np.unique(_safe_indexing(X, feature, axis=1))
            except TypeError as exc:
                # `np.unique` will fail in the presence of `np.nan` and `str` categories
                # due to sorting. Temporary, we reraise an error explaining the problem.
                raise ValueError(
                    f"The column #{feature} contains mixed data types. Finding unique "
                    "categories fail due to sorting. It usually means that the column "
                    "contains `np.nan` values together with `str` categories. Such use "
                    "case is not yet supported in scikit-learn."
                ) from exc

            if is_cat or uniques.shape[0] < grid_resolution:
                # Use the unique values either because:
                # - feature has low resolution use unique values
                # - feature is categorical
                axis = uniques
            else:
                # create axis based on percentiles and grid resolution
                emp_percentiles = mquantiles(
                    _safe_indexing(X, feature, axis=1), prob=percentiles, axis=0
                )
                if np.allclose(emp_percentiles[0], emp_percentiles[1]):
                    raise ValueError(
                        "percentiles are too close to each other, "
                        "unable to build the grid. Please choose percentiles "
                        "that are further apart."
                    )
                axis = np.linspace(
                    emp_percentiles[0],
                    emp_percentiles[1],
                    num=grid_resolution,
                    endpoint=True,
                )
        values.append(axis)

    return cartesian(values), values