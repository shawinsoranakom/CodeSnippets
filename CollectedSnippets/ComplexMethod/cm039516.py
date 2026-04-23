def test_roc_curve_chance_level_line(
    pyplot,
    data_binary,
    plot_chance_level,
    chance_level_kw,
    label,
    constructor_name,
):
    """Check chance level plotting behavior of `from_predictions`, `from_estimator`."""
    X, y = data_binary

    lr = LogisticRegression()
    lr.fit(X, y)

    y_score = getattr(lr, "predict_proba")(X)
    y_score = y_score if y_score.ndim == 1 else y_score[:, 1]

    if constructor_name == "from_estimator":
        display = RocCurveDisplay.from_estimator(
            lr,
            X,
            y,
            curve_kwargs={"alpha": 0.8, "label": label},
            plot_chance_level=plot_chance_level,
            chance_level_kw=chance_level_kw,
        )
    else:
        display = RocCurveDisplay.from_predictions(
            y,
            y_score,
            curve_kwargs={"alpha": 0.8, "label": label},
            plot_chance_level=plot_chance_level,
            chance_level_kw=chance_level_kw,
        )

    import matplotlib as mpl

    assert isinstance(display.line_, mpl.lines.Line2D)
    assert display.line_.get_alpha() == 0.8
    assert isinstance(display.ax_, mpl.axes.Axes)
    assert isinstance(display.figure_, mpl.figure.Figure)

    _check_chance_level(plot_chance_level, chance_level_kw, display)

    # Checking for legend behaviour
    if plot_chance_level and chance_level_kw is not None:
        if label is not None or chance_level_kw.get("label") is not None:
            legend = display.ax_.get_legend()
            assert legend is not None  #  Legend should be present if any label is set
            legend_labels = [text.get_text() for text in legend.get_texts()]
            if label is not None:
                assert label in legend_labels
            if chance_level_kw.get("label") is not None:
                assert chance_level_kw["label"] in legend_labels
        else:
            assert display.ax_.get_legend() is None