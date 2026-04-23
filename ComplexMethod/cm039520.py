def test_precision_recall_display_plotting(
    pyplot,
    constructor_name,
    response_method,
    drop_intermediate,
    with_sample_weight,
):
    """Check the overall plotting rendering."""
    import matplotlib as mpl

    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)
    pos_label = 1

    classifier = LogisticRegression().fit(X, y)
    classifier.fit(X, y)

    if with_sample_weight:
        rng = np.random.RandomState(42)
        sample_weight = rng.randint(1, 4, size=(X.shape[0]))
    else:
        sample_weight = None

    y_score = getattr(classifier, response_method)(X)
    y_score = y_score if y_score.ndim == 1 else y_score[:, pos_label]

    # safe guard for the binary if/else construction
    assert constructor_name in ("from_estimator", "from_predictions")

    if constructor_name == "from_estimator":
        display = PrecisionRecallDisplay.from_estimator(
            classifier,
            X,
            y,
            sample_weight=sample_weight,
            response_method=response_method,
            drop_intermediate=drop_intermediate,
        )
    else:
        display = PrecisionRecallDisplay.from_predictions(
            y,
            y_score,
            sample_weight=sample_weight,
            pos_label=pos_label,
            drop_intermediate=drop_intermediate,
        )

    precision, recall, _ = precision_recall_curve(
        y,
        y_score,
        pos_label=pos_label,
        sample_weight=sample_weight,
        drop_intermediate=drop_intermediate,
    )
    average_precision = average_precision_score(
        y, y_score, pos_label=pos_label, sample_weight=sample_weight
    )

    assert_allclose(display.precision, precision)
    assert_allclose(display.recall, recall)
    assert display.average_precision == pytest.approx(average_precision)

    _check_figure_axes_and_labels(display, pos_label)
    assert isinstance(display.line_, mpl.lines.Line2D)
    # Check default curve kwarg
    assert display.line_.get_drawstyle() == "steps-post"

    # plotting passing some new parameters
    display.plot(name="MySpecialEstimator", curve_kwargs={"alpha": 0.8})
    expected_label = f"MySpecialEstimator (AP = {average_precision:0.2f})"
    assert display.line_.get_label() == expected_label
    assert display.line_.get_alpha() == pytest.approx(0.8)

    # Check that the chance level line is not plotted by default
    assert display.chance_level_ is None