def test_partial_roc_auc_score():
    # Check `roc_auc_score` for max_fpr != `None`
    y_true = np.array([0, 0, 1, 1])
    assert roc_auc_score(y_true, y_true, max_fpr=1) == 1
    assert roc_auc_score(y_true, y_true, max_fpr=0.001) == 1
    with pytest.raises(ValueError):
        assert roc_auc_score(y_true, y_true, max_fpr=-0.1)
    with pytest.raises(ValueError):
        assert roc_auc_score(y_true, y_true, max_fpr=1.1)
    with pytest.raises(ValueError):
        assert roc_auc_score(y_true, y_true, max_fpr=0)

    y_scores = np.array([0.1, 0, 0.1, 0.01])
    roc_auc_with_max_fpr_one = roc_auc_score(y_true, y_scores, max_fpr=1)
    unconstrained_roc_auc = roc_auc_score(y_true, y_scores)
    assert roc_auc_with_max_fpr_one == unconstrained_roc_auc
    assert roc_auc_score(y_true, y_scores, max_fpr=0.3) == 0.5

    y_true, y_pred, _ = make_prediction(binary=True)
    for max_fpr in np.linspace(1e-4, 1, 5):
        assert_almost_equal(
            roc_auc_score(y_true, y_pred, max_fpr=max_fpr),
            _partial_roc_auc_score(y_true, y_pred, max_fpr),
        )