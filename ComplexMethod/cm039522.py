def test_precision_recall_chance_level_line(
    pyplot, plot_chance_level, chance_level_kw, constructor_name
):
    """Check chance level plotting behavior, for `from_estimator`/`from_predictions`."""
    import matplotlib as mpl

    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)
    pos_prevalence = Counter(y)[1] / len(y)

    lr = LogisticRegression()
    y_score = lr.fit(X, y).predict_proba(X)[:, 1]

    if constructor_name == "from_estimator":
        display = PrecisionRecallDisplay.from_estimator(
            lr,
            X,
            y,
            plot_chance_level=plot_chance_level,
            chance_level_kw=chance_level_kw,
        )
    else:
        display = PrecisionRecallDisplay.from_predictions(
            y,
            y_score,
            plot_chance_level=plot_chance_level,
            chance_level_kw=chance_level_kw,
        )

    if not plot_chance_level:
        assert display.chance_level_ is None
        # Early return if chance level not plotted
        return

    assert isinstance(display.chance_level_, mpl.lines.Line2D)
    assert tuple(display.chance_level_.get_xdata()) == (0, 1)
    assert tuple(display.chance_level_.get_ydata()) == (pos_prevalence, pos_prevalence)

    # Checking for chance level line styles
    if chance_level_kw is None:
        assert display.chance_level_.get_color() == "k"
    else:
        assert display.chance_level_.get_color() == "r"

    assert display.chance_level_.get_label() == f"Chance level (AP = {pos_prevalence})"