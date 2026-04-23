def test_plot_partial_dependence_custom_axes(
    use_custom_values, pyplot, clf_diabetes, diabetes
):
    grid_resolution = 25
    fig, (ax1, ax2) = pyplot.subplots(1, 2)

    age = diabetes.data[:, diabetes.feature_names.index("age")]
    bmi = diabetes.data[:, diabetes.feature_names.index("bmi")]
    custom_values = None
    if use_custom_values:
        custom_values = {
            "age": custom_values_helper(age, grid_resolution),
            "bmi": custom_values_helper(bmi, grid_resolution),
        }

    disp = PartialDependenceDisplay.from_estimator(
        clf_diabetes,
        diabetes.data,
        ["age", ("age", "bmi")],
        grid_resolution=grid_resolution,
        feature_names=diabetes.feature_names,
        ax=[ax1, ax2],
        custom_values=custom_values,
    )
    assert fig is disp.figure_
    assert disp.bounding_ax_ is None
    assert disp.axes_.shape == (2,)
    assert disp.axes_[0] is ax1
    assert disp.axes_[1] is ax2

    ax = disp.axes_[0]
    assert ax.get_xlabel() == "age"
    assert ax.get_ylabel() == "Partial dependence"

    line = disp.lines_[0]
    avg_preds = disp.pd_results[0]
    target_idx = disp.target_idx

    line_data = line.get_data()
    assert_allclose(line_data[0], avg_preds["grid_values"][0])
    assert_allclose(line_data[1], avg_preds.average[target_idx].ravel())

    # contour
    ax = disp.axes_[1]
    assert ax.get_xlabel() == "age"
    assert ax.get_ylabel() == "bmi"