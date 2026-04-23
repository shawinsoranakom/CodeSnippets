def test_plot_partial_dependence_lines_kw(
    pyplot,
    clf_diabetes,
    diabetes,
    line_kw,
    pd_line_kw,
    ice_lines_kw,
    expected_colors,
):
    """Check that passing `pd_line_kw` and `ice_lines_kw` will act on the
    specific lines in the plot.
    """

    disp = PartialDependenceDisplay.from_estimator(
        clf_diabetes,
        diabetes.data,
        [0, 2],
        grid_resolution=20,
        feature_names=diabetes.feature_names,
        n_cols=2,
        kind="both",
        line_kw=line_kw,
        pd_line_kw=pd_line_kw,
        ice_lines_kw=ice_lines_kw,
    )

    line = disp.lines_[0, 0, -1]
    assert line.get_color() == expected_colors[0], (
        f"{line.get_color()}!={expected_colors[0]}\n{line_kw} and {pd_line_kw}"
    )
    if pd_line_kw is not None:
        if "linestyle" in pd_line_kw:
            assert line.get_linestyle() == pd_line_kw["linestyle"]
        elif "ls" in pd_line_kw:
            assert line.get_linestyle() == pd_line_kw["ls"]
    else:
        assert line.get_linestyle() == "--"

    line = disp.lines_[0, 0, 0]
    assert line.get_color() == expected_colors[1], (
        f"{line.get_color()}!={expected_colors[1]}"
    )
    if ice_lines_kw is not None:
        if "linestyle" in ice_lines_kw:
            assert line.get_linestyle() == ice_lines_kw["linestyle"]
        elif "ls" in ice_lines_kw:
            assert line.get_linestyle() == ice_lines_kw["ls"]
    else:
        assert line.get_linestyle() == "-"