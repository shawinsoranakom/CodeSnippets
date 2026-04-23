def test_plot_partial_dependence_multioutput(use_custom_values, pyplot, target):
    # Test partial dependence plot function on multi-output input.
    X, y = multioutput_regression_data
    clf = LinearRegression().fit(X, y)

    grid_resolution = 25

    custom_values = None
    if use_custom_values:
        custom_values = {
            0: custom_values_helper(X[:, 0], grid_resolution),
            1: custom_values_helper(X[:, 1], grid_resolution),
        }

    disp = PartialDependenceDisplay.from_estimator(
        clf,
        X,
        [0, 1],
        target=target,
        grid_resolution=grid_resolution,
        custom_values=custom_values,
    )
    fig = pyplot.gcf()
    axs = fig.get_axes()
    assert len(axs) == 3
    assert disp.target_idx == target
    assert disp.bounding_ax_ is not None

    positions = [(0, 0), (0, 1)]
    expected_label = ["Partial dependence", ""]

    for i, pos in enumerate(positions):
        ax = disp.axes_[pos]
        assert ax.get_ylabel() == expected_label[i]
        assert ax.get_xlabel() == f"x{i}"