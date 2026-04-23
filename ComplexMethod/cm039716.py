def check_cv_results_array_types(
    search, param_keys, score_keys, expected_cv_results_kinds
):
    # Check if the search `cv_results`'s array are of correct types
    cv_results = search.cv_results_
    assert all(isinstance(cv_results[param], np.ma.MaskedArray) for param in param_keys)
    assert {
        key: cv_results[key].dtype.kind for key in param_keys
    } == expected_cv_results_kinds
    assert not any(isinstance(cv_results[key], np.ma.MaskedArray) for key in score_keys)
    assert all(
        cv_results[key].dtype == np.float64
        for key in score_keys
        if not key.startswith("rank")
    )

    scorer_keys = search.scorer_.keys() if search.multimetric_ else ["score"]

    for key in scorer_keys:
        assert cv_results["rank_test_%s" % key].dtype == np.int32