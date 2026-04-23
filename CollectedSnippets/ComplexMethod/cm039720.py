def compare_refit_methods_when_refit_with_acc(search_multi, search_acc, refit):
    """Compare refit multi-metric search methods with single metric methods"""
    assert search_acc.refit == refit
    if refit:
        assert search_multi.refit == "accuracy"
    else:
        assert not search_multi.refit
        return  # search cannot predict/score without refit

    X, y = make_blobs(n_samples=100, n_features=4, random_state=42)
    for method in ("predict", "predict_proba", "predict_log_proba"):
        assert_almost_equal(
            getattr(search_multi, method)(X), getattr(search_acc, method)(X)
        )
    assert_almost_equal(search_multi.score(X, y), search_acc.score(X, y))
    for key in ("best_index_", "best_score_", "best_params_"):
        assert getattr(search_multi, key) == getattr(search_acc, key)