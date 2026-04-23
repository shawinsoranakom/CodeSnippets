def test_roc_curve_display_plotting(
    pyplot,
    response_method,
    data_binary,
    with_sample_weight,
    drop_intermediate,
    with_strings,
    constructor_name,
    default_name,
):
    """Check the overall plotting behaviour for single curve."""
    X, y = data_binary

    pos_label = None
    if with_strings:
        y = np.array(["c", "b"])[y]
        pos_label = "c"

    if with_sample_weight:
        rng = np.random.RandomState(42)
        sample_weight = rng.randint(1, 4, size=(X.shape[0]))
    else:
        sample_weight = None

    lr = LogisticRegression()
    lr.fit(X, y)

    y_score = getattr(lr, response_method)(X)
    y_score = y_score if y_score.ndim == 1 else y_score[:, 1]

    if constructor_name == "from_estimator":
        display = RocCurveDisplay.from_estimator(
            lr,
            X,
            y,
            sample_weight=sample_weight,
            drop_intermediate=drop_intermediate,
            pos_label=pos_label,
            curve_kwargs={"alpha": 0.8},
        )
    else:
        display = RocCurveDisplay.from_predictions(
            y,
            y_score,
            sample_weight=sample_weight,
            drop_intermediate=drop_intermediate,
            pos_label=pos_label,
            curve_kwargs={"alpha": 0.8},
        )

    fpr, tpr, _ = roc_curve(
        y,
        y_score,
        sample_weight=sample_weight,
        drop_intermediate=drop_intermediate,
        pos_label=pos_label,
    )

    assert_allclose(display.roc_auc, auc(fpr, tpr))
    assert_allclose(display.fpr, fpr)
    assert_allclose(display.tpr, tpr)

    assert display.name == default_name

    import matplotlib as mpl

    _check_figure_axes_and_labels(display, pos_label)
    assert isinstance(display.line_, mpl.lines.Line2D)
    assert display.line_.get_alpha() == 0.8

    expected_label = f"{default_name} (AUC = {display.roc_auc:.2f})"
    assert display.line_.get_label() == expected_label