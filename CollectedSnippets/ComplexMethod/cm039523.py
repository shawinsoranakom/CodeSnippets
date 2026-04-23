def test_precision_recall_chance_level_line_from_cv_results(
    pyplot, plot_chance_level, chance_level_kw
):
    """Check chance level plotting behavior for `from_cv_results`."""
    import matplotlib as mpl

    # Note a separate chance line is plotted for each cv split
    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)
    n_cv = 3
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=n_cv, return_estimator=True, return_indices=True
    )

    display = PrecisionRecallDisplay.from_cv_results(
        cv_results,
        X,
        y,
        plot_chance_level=plot_chance_level,
        chance_level_kwargs=chance_level_kw,
    )

    if not plot_chance_level:
        assert display.chance_level_ is None
        # Early return if chance level not plotted
        return

    pos_prevalence_folds = []
    for idx in range(n_cv):
        assert isinstance(display.chance_level_[idx], mpl.lines.Line2D)
        assert tuple(display.chance_level_[idx].get_xdata()) == (0, 1)
        test_indices = cv_results["indices"]["test"][idx]
        pos_prevalence = Counter(_safe_indexing(y, test_indices))[1] / len(test_indices)
        pos_prevalence_folds.append(pos_prevalence)
        assert tuple(display.chance_level_[idx].get_ydata()) == (
            pos_prevalence,
            pos_prevalence,
        )

        # Checking for chance level line styles
        if chance_level_kw is None:
            assert display.chance_level_[idx].get_color() == "k"
        else:
            assert display.chance_level_[idx].get_color() == "r"

    for idx in range(n_cv):
        # Only the first chance line should have a label
        if idx == 0:
            assert display.chance_level_[idx].get_label() == (
                f"Chance level (AP = {np.mean(pos_prevalence_folds):0.2f} +/- "
                f"{np.std(pos_prevalence_folds):0.2f})"
            )
        else:
            assert display.chance_level_[idx].get_label() == f"_child{3 + idx}"