def test_grid_from_X():
    # tests for _grid_from_X: sanity check for output, and for shapes.

    # Make sure that the grid is a cartesian product of the input (it will use
    # the unique values instead of the percentiles)
    percentiles = (0.05, 0.95)
    grid_resolution = 100
    is_categorical = [False, False]
    X = np.asarray([[1, 2], [3, 4]])
    grid, axes = _grid_from_X(X, percentiles, is_categorical, grid_resolution, {})
    assert_array_equal(grid, [[1, 2], [1, 4], [3, 2], [3, 4]])
    assert_array_equal(axes, X.T)

    # test shapes of returned objects depending on the number of unique values
    # for a feature.
    rng = np.random.RandomState(0)
    grid_resolution = 15

    # n_unique_values > grid_resolution
    X = rng.normal(size=(20, 2))
    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical,
        grid_resolution=grid_resolution,
        custom_values={},
    )
    assert grid.shape == (grid_resolution * grid_resolution, X.shape[1])
    assert np.asarray(axes).shape == (2, grid_resolution)
    assert grid.dtype == X.dtype

    # n_unique_values < grid_resolution, will use actual values
    n_unique_values = 12
    X[n_unique_values - 1 :, 0] = 12345
    rng.shuffle(X)  # just to make sure the order is irrelevant
    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical,
        grid_resolution=grid_resolution,
        custom_values={},
    )
    assert grid.shape == (n_unique_values * grid_resolution, X.shape[1])
    # axes is a list of arrays of different shapes
    assert axes[0].shape == (n_unique_values,)
    assert axes[1].shape == (grid_resolution,)
    assert grid.dtype == X.dtype

    # Check that uses custom_range
    X = rng.normal(size=(20, 2))
    X[n_unique_values - 1 :, 0] = 12345
    col_1_range = [0, 2, 3]
    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical=is_categorical,
        grid_resolution=grid_resolution,
        custom_values={1: col_1_range},
    )
    assert grid.shape == (n_unique_values * len(col_1_range), X.shape[1])
    # axes is a list of arrays of different shapes
    assert axes[0].shape == (n_unique_values,)
    assert axes[1].shape == (len(col_1_range),)
    assert grid.dtype == X.dtype

    # Check that grid_resolution does not impact custom_range
    X = rng.normal(size=(20, 2))
    col_0_range = [0, 2, 3, 4, 5, 6]
    grid_resolution = 5
    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical=is_categorical,
        grid_resolution=grid_resolution,
        custom_values={0: col_0_range},
    )
    assert grid.shape == (grid_resolution * len(col_0_range), X.shape[1])
    # axes is a list of arrays of different shapes
    assert axes[0].shape == (len(col_0_range),)
    assert axes[1].shape == (grid_resolution,)
    assert grid.dtype == np.result_type(X, np.asarray(col_0_range).dtype)

    X = np.array([[0, "a"], [1, "b"], [2, "c"]])

    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical=is_categorical,
        grid_resolution=grid_resolution,
        custom_values={1: ["a", "b", "c"]},
    )
    assert grid.dtype == object