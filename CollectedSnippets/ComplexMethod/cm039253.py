def test_plot_partial_dependence_passing_numpy_axes(
    pyplot,
    clf_diabetes,
    diabetes,
    use_custom_values,
    kind,
    lines,
):
    grid_resolution = 25
    feature_names = diabetes.feature_names

    age = diabetes.data[:, diabetes.feature_names.index("age")]
    bmi = diabetes.data[:, diabetes.feature_names.index("bmi")]
    custom_values = None
    if use_custom_values:
        custom_values = {
            "age": custom_values_helper(age, grid_resolution),
            "bmi": custom_values_helper(bmi, grid_resolution),
        }

    disp1 = PartialDependenceDisplay.from_estimator(
        clf_diabetes,
        diabetes.data,
        ["age", "bmi"],
        kind=kind,
        grid_resolution=grid_resolution,
        feature_names=feature_names,
        custom_values=custom_values,
    )
    assert disp1.axes_.shape == (1, 2)
    assert disp1.axes_[0, 0].get_ylabel() == "Partial dependence"
    assert disp1.axes_[0, 1].get_ylabel() == ""
    assert len(disp1.axes_[0, 0].get_lines()) == lines
    assert len(disp1.axes_[0, 1].get_lines()) == lines

    lr = LinearRegression()
    lr.fit(diabetes.data, diabetes.target)

    disp2 = PartialDependenceDisplay.from_estimator(
        lr,
        diabetes.data,
        ["age", "bmi"],
        kind=kind,
        grid_resolution=grid_resolution,
        feature_names=feature_names,
        ax=disp1.axes_,
    )

    assert np.all(disp1.axes_ == disp2.axes_)
    assert len(disp2.axes_[0, 0].get_lines()) == 2 * lines
    assert len(disp2.axes_[0, 1].get_lines()) == 2 * lines