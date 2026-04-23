def test_curve_display_negate_score(pyplot, data, CurveDisplay, specific_params):
    """Check the behaviour of the `negate_score` parameter calling `from_estimator` and
    `plot`.
    """
    X, y = data
    estimator = DecisionTreeClassifier(max_depth=1, random_state=0)

    negate_score = False
    display = CurveDisplay.from_estimator(
        estimator, X, y, **specific_params, negate_score=negate_score
    )

    positive_scores = display.lines_[0].get_data()[1]
    assert (positive_scores >= 0).all()
    assert display.ax_.get_ylabel() == "Score"

    negate_score = True
    display = CurveDisplay.from_estimator(
        estimator, X, y, **specific_params, negate_score=negate_score
    )

    negative_scores = display.lines_[0].get_data()[1]
    assert (negative_scores <= 0).all()
    assert_allclose(negative_scores, -positive_scores)
    assert display.ax_.get_ylabel() == "Negative score"

    negate_score = False
    display = CurveDisplay.from_estimator(
        estimator, X, y, **specific_params, negate_score=negate_score
    )
    assert display.ax_.get_ylabel() == "Score"
    display.plot(negate_score=not negate_score)
    assert display.ax_.get_ylabel() == "Score"
    assert (display.lines_[0].get_data()[1] < 0).all()