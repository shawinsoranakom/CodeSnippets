def test_roc_curve_chance_level_line_from_cv_results(
    pyplot,
    data_binary,
    plot_chance_level,
    chance_level_kw,
    curve_kwargs,
):
    """Check chance level plotting behavior with `from_cv_results`."""
    X, y = data_binary
    n_cv = 3
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=n_cv, return_estimator=True, return_indices=True
    )

    display = RocCurveDisplay.from_cv_results(
        cv_results,
        X,
        y,
        plot_chance_level=plot_chance_level,
        chance_level_kwargs=chance_level_kw,
        curve_kwargs=curve_kwargs,
    )

    import matplotlib as mpl

    assert all(isinstance(line, mpl.lines.Line2D) for line in display.line_)
    # Ensure both curve line kwargs passed correctly as well
    if curve_kwargs:
        assert all(line.get_alpha() == 0.8 for line in display.line_)
    assert isinstance(display.ax_, mpl.axes.Axes)
    assert isinstance(display.figure_, mpl.figure.Figure)

    _check_chance_level(plot_chance_level, chance_level_kw, display)

    legend = display.ax_.get_legend()
    # There is always a legend, to indicate each 'Fold' curve
    assert legend is not None
    legend_labels = [text.get_text() for text in legend.get_texts()]
    if plot_chance_level and chance_level_kw is not None:
        if chance_level_kw.get("label") is not None:
            assert chance_level_kw["label"] in legend_labels
        else:
            assert len(legend_labels) == 1