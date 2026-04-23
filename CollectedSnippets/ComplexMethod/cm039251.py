def test_plot_partial_dependence_str_features(
    pyplot,
    use_custom_values,
    clf_diabetes,
    diabetes,
    input_type,
    feature_names_type,
):
    age = diabetes.data[:, diabetes.feature_names.index("age")]
    bmi = diabetes.data[:, diabetes.feature_names.index("bmi")]

    if input_type == "dataframe":
        pd = pytest.importorskip("pandas")
        X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
    elif input_type == "list":
        X = diabetes.data.tolist()
    else:
        X = diabetes.data

    if feature_names_type is None:
        feature_names = None
    else:
        feature_names = _convert_container(diabetes.feature_names, feature_names_type)

    grid_resolution = 25
    custom_values = None
    if use_custom_values:
        custom_values = {
            "age": custom_values_helper(age, grid_resolution),
            "bmi": custom_values_helper(bmi, grid_resolution),
        }
    # check with str features and array feature names and single column
    disp = PartialDependenceDisplay.from_estimator(
        clf_diabetes,
        X,
        [("age", "bmi"), "bmi"],
        grid_resolution=grid_resolution,
        feature_names=feature_names,
        n_cols=1,
        line_kw={"alpha": 0.8},
        custom_values=custom_values,
    )
    fig = pyplot.gcf()
    axs = fig.get_axes()
    assert len(axs) == 3

    assert disp.figure_ is fig
    assert disp.axes_.shape == (2, 1)
    assert disp.lines_.shape == (2, 1)
    assert disp.contours_.shape == (2, 1)
    assert disp.deciles_vlines_.shape == (2, 1)
    assert disp.deciles_hlines_.shape == (2, 1)

    assert disp.lines_[0, 0] is None
    assert disp.deciles_vlines_[0, 0] is not None
    assert disp.deciles_hlines_[0, 0] is not None
    assert disp.contours_[1, 0] is None
    assert disp.deciles_hlines_[1, 0] is None
    assert disp.deciles_vlines_[1, 0] is not None

    # line
    ax = disp.axes_[1, 0]
    assert ax.get_xlabel() == "bmi"
    assert ax.get_ylabel() == "Partial dependence"

    line = disp.lines_[1, 0]
    avg_preds = disp.pd_results[1]
    target_idx = disp.target_idx
    assert line.get_alpha() == 0.8

    line_data = line.get_data()
    assert_allclose(line_data[0], avg_preds["grid_values"][0])
    assert_allclose(line_data[1], avg_preds.average[target_idx].ravel())

    # contour
    ax = disp.axes_[0, 0]
    assert ax.get_xlabel() == "age"
    assert ax.get_ylabel() == "bmi"