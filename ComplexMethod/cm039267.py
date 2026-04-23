def test_grid_from_X_heterogeneous_type(grid_resolution):
    """Check that `_grid_from_X` always sample from categories and does not
    depend from the percentiles.
    """
    pd = pytest.importorskip("pandas")
    percentiles = (0.05, 0.95)
    is_categorical = [True, False]
    X = pd.DataFrame(
        {
            "cat": ["A", "B", "C", "A", "B", "D", "E", "A", "B", "D"],
            "num": [1, 1, 1, 2, 5, 6, 6, 6, 6, 8],
        }
    )
    nunique = X.nunique()

    grid, axes = _grid_from_X(
        X,
        percentiles,
        is_categorical,
        grid_resolution=grid_resolution,
        custom_values={},
    )
    if grid_resolution == 3:
        assert grid.shape == (15, 2)
        assert axes[0].shape[0] == nunique["num"]
        assert axes[1].shape[0] == grid_resolution
    else:
        assert grid.shape == (25, 2)
        assert axes[0].shape[0] == nunique["cat"]
        assert axes[1].shape[0] == nunique["cat"]