def test_d2_brier_score():
    """Test that d2_brier_score gives expected outcomes in both the binary and
    multiclass settings.
    """
    # Binary targets
    sample_weight = [2, 2, 3, 1, 1, 1]
    y_true = [0, 1, 1, 0, 0, 1]
    y_true_string = ["no", "yes", "yes", "no", "no", "yes"]

    # check that the value of the returned d2 score is correct
    y_proba = [0.3, 0.5, 0.6, 0.7, 0.9, 0.8]
    y_proba_ref = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    d2_score = d2_brier_score(y_true=y_true, y_proba=y_proba)
    brier_score_model = brier_score_loss(y_true=y_true, y_proba=y_proba)
    brier_score_ref = brier_score_loss(y_true=y_true, y_proba=y_proba_ref)
    d2_score_expected = 1 - brier_score_model / brier_score_ref
    assert pytest.approx(d2_score) == d2_score_expected

    # check that a model which gives a constant prediction equal to the
    # proportion of the positive class should get a d2 score of 0
    y_proba = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    d2_score = d2_brier_score(y_true=y_true, y_proba=y_proba)
    assert d2_score == 0
    d2_score = d2_brier_score(y_true=y_true_string, y_proba=y_proba, pos_label="yes")
    assert d2_score == 0

    # check that a model which gives a constant prediction equal to the
    # proportion of the positive class should get a d2 score of 0
    # when we also provide sample weight
    y_proba = [0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
    d2_score = d2_brier_score(
        y_true=y_true, y_proba=y_proba, sample_weight=sample_weight
    )
    assert d2_score == 0
    d2_score = d2_brier_score(
        y_true=y_true_string,
        y_proba=y_proba,
        sample_weight=sample_weight,
        pos_label="yes",
    )
    assert d2_score == 0

    # Multiclass targets
    sample_weight = [2, 1, 3, 1, 1, 2, 1, 4, 1, 4]
    y_true = [3, 3, 2, 2, 2, 1, 1, 1, 1, 0]
    y_true_string = ["dd", "dd", "cc", "cc", "cc", "bb", "bb", "bb", "bb", "aa"]

    # check that a model which gives a constant prediction equal to the
    # proportion of the given labels gives a d2 score of 0 when we also
    # provide sample weight
    y_proba = [
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
        [0.2, 0.4, 0.25, 0.15],
    ]
    d2_score = d2_brier_score(
        y_true=y_true, y_proba=y_proba, sample_weight=sample_weight
    )
    assert d2_score == 0
    d2_score = d2_brier_score(
        y_true=y_true_string,
        y_proba=y_proba,
        sample_weight=sample_weight,
    )
    assert d2_score == 0

    # check that a model which gives generally good predictions has
    # a d2 score that is greater than 0.5
    y_proba = [
        [0.1, 0.2, 0.2, 0.5],
        [0.1, 0.2, 0.2, 0.5],
        [0.1, 0.2, 0.5, 0.2],
        [0.1, 0.2, 0.5, 0.2],
        [0.1, 0.2, 0.5, 0.2],
        [0.2, 0.5, 0.2, 0.1],
        [0.2, 0.5, 0.2, 0.1],
        [0.2, 0.5, 0.2, 0.1],
        [0.2, 0.5, 0.2, 0.1],
        [0.5, 0.2, 0.2, 0.1],
    ]
    d2_score = d2_brier_score(
        y_true=y_true, y_proba=y_proba, sample_weight=sample_weight
    )
    assert d2_score > 0.5
    d2_score = d2_brier_score(
        y_true=y_true_string,
        y_proba=y_proba,
        sample_weight=sample_weight,
    )
    assert d2_score > 0.5