def test_d2_log_loss_score():
    y_true = [0, 0, 0, 1, 1, 1]
    y_true_string = ["no", "no", "no", "yes", "yes", "yes"]
    y_proba = np.array(
        [
            [0.5, 0.5],
            [0.9, 0.1],
            [0.4, 0.6],
            [0.6, 0.4],
            [0.35, 0.65],
            [0.01, 0.99],
        ]
    )
    y_proba_null = np.array(
        [
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
        ]
    )
    d2_score = d2_log_loss_score(y_true=y_true, y_proba=y_proba)
    log_likelihood = log_loss(y_true=y_true, y_proba=y_proba, normalize=False)
    log_likelihood_null = log_loss(y_true=y_true, y_proba=y_proba_null, normalize=False)
    d2_score_true = 1 - log_likelihood / log_likelihood_null
    assert d2_score == pytest.approx(d2_score_true)

    # check that using sample weight also gives the correct d2 score
    sample_weight = np.array([2, 1, 3, 4, 3, 1])
    y_proba_null[:, 0] = sample_weight[:3].sum() / sample_weight.sum()
    y_proba_null[:, 1] = sample_weight[3:].sum() / sample_weight.sum()
    d2_score = d2_log_loss_score(
        y_true=y_true, y_proba=y_proba, sample_weight=sample_weight
    )
    log_likelihood = log_loss(
        y_true=y_true,
        y_proba=y_proba,
        sample_weight=sample_weight,
        normalize=False,
    )
    log_likelihood_null = log_loss(
        y_true=y_true,
        y_proba=y_proba_null,
        sample_weight=sample_weight,
        normalize=False,
    )
    d2_score_true = 1 - log_likelihood / log_likelihood_null
    assert d2_score == pytest.approx(d2_score_true)

    # check if good predictions give a relatively higher value for the d2 score
    y_proba = np.array(
        [
            [0.9, 0.1],
            [0.8, 0.2],
            [0.9, 0.1],
            [0.1, 0.9],
            [0.2, 0.8],
            [0.1, 0.9],
        ]
    )
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert 0.5 < d2_score < 1.0
    # check that a similar value is obtained for string labels
    d2_score_string = d2_log_loss_score(y_true_string, y_proba)
    assert d2_score_string == pytest.approx(d2_score)

    # check if poor predictions gives a relatively low value for the d2 score
    y_proba = np.array(
        [
            [0.5, 0.5],
            [0.1, 0.9],
            [0.1, 0.9],
            [0.9, 0.1],
            [0.75, 0.25],
            [0.1, 0.9],
        ]
    )
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert d2_score < 0
    # check that a similar value is obtained for string labels
    d2_score_string = d2_log_loss_score(y_true_string, y_proba)
    assert d2_score_string == pytest.approx(d2_score)

    # check if simply using the average of the classes as the predictions
    # gives a d2 score of 0
    y_true = [0, 0, 0, 1, 1, 1]
    y_proba = np.array(
        [
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
            [0.5, 0.5],
        ]
    )
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert d2_score == 0
    d2_score_string = d2_log_loss_score(y_true_string, y_proba)
    assert d2_score_string == 0

    # check if simply using the average of the classes as the predictions
    # gives a d2 score of 0 when the positive class has a higher proportion
    y_true = [0, 1, 1, 1]
    y_true_string = ["no", "yes", "yes", "yes"]
    y_proba = np.array([[0.25, 0.75], [0.25, 0.75], [0.25, 0.75], [0.25, 0.75]])
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert d2_score == 0
    d2_score_string = d2_log_loss_score(y_true_string, y_proba)
    assert d2_score_string == 0
    sample_weight = [2, 2, 2, 2]
    d2_score_with_sample_weight = d2_log_loss_score(
        y_true, y_proba, sample_weight=sample_weight
    )
    assert d2_score_with_sample_weight == 0

    # check that the d2 scores seem correct when more than 2
    # labels are specified
    y_true = ["high", "high", "low", "neutral"]
    sample_weight = [1.4, 0.6, 0.8, 0.2]

    y_proba = np.array(
        [
            [0.8, 0.1, 0.1],
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
        ]
    )
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert 0.5 < d2_score < 1.0
    d2_score = d2_log_loss_score(y_true, y_proba, sample_weight=sample_weight)
    assert 0.5 < d2_score < 1.0

    y_proba = np.array(
        [
            [0.2, 0.5, 0.3],
            [0.1, 0.7, 0.2],
            [0.1, 0.1, 0.8],
            [0.2, 0.7, 0.1],
        ]
    )
    d2_score = d2_log_loss_score(y_true, y_proba)
    assert d2_score < 0
    d2_score = d2_log_loss_score(y_true, y_proba, sample_weight=sample_weight)
    assert d2_score < 0