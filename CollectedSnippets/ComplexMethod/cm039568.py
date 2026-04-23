def _test_ndcg_score_for(y_true, y_score):
    ideal = _ndcg_sample_scores(y_true, y_true)
    score = _ndcg_sample_scores(y_true, y_score)
    assert (score <= ideal).all()
    all_zero = (y_true == 0).all(axis=1)
    assert ideal[~all_zero] == pytest.approx(np.ones((~all_zero).sum()))
    assert ideal[all_zero] == pytest.approx(np.zeros(all_zero.sum()))
    assert score[~all_zero] == pytest.approx(
        _dcg_sample_scores(y_true, y_score)[~all_zero]
        / _dcg_sample_scores(y_true, y_true)[~all_zero]
    )
    assert score[all_zero] == pytest.approx(np.zeros(all_zero.sum()))
    assert ideal.shape == (y_true.shape[0],)
    assert score.shape == (y_true.shape[0],)