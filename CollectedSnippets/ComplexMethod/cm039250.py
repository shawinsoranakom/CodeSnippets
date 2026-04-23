def test_plot_partial_dependence_kind(
    pyplot,
    kind,
    centered,
    subsample,
    shape,
    clf_diabetes,
    diabetes,
):
    disp = PartialDependenceDisplay.from_estimator(
        clf_diabetes,
        diabetes.data,
        [0, 1, 2],
        kind=kind,
        centered=centered,
        subsample=subsample,
    )

    assert disp.axes_.shape == (1, 3)
    assert disp.lines_.shape == shape
    assert disp.contours_.shape == (1, 3)

    assert disp.contours_[0, 0] is None
    assert disp.contours_[0, 1] is None
    assert disp.contours_[0, 2] is None

    if centered:
        assert all([ln._y[0] == 0.0 for ln in disp.lines_.ravel() if ln is not None])
    else:
        assert all([ln._y[0] != 0.0 for ln in disp.lines_.ravel() if ln is not None])