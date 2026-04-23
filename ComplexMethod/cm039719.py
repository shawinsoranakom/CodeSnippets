def compare_cv_results_multimetric_with_single(search_multi, search_acc, search_rec):
    """Compare multi-metric cv_results with the ensemble of multiple
    single metric cv_results from single metric grid/random search"""

    assert search_multi.multimetric_
    assert_array_equal(sorted(search_multi.scorer_), ("accuracy", "recall"))

    cv_results_multi = search_multi.cv_results_
    cv_results_acc_rec = {
        re.sub("_score$", "_accuracy", k): v for k, v in search_acc.cv_results_.items()
    }
    cv_results_acc_rec.update(
        {re.sub("_score$", "_recall", k): v for k, v in search_rec.cv_results_.items()}
    )

    # Check if score and timing are reasonable, also checks if the keys
    # are present
    assert all(
        (
            np.all(cv_results_multi[k] <= 1)
            for k in (
                "mean_score_time",
                "std_score_time",
                "mean_fit_time",
                "std_fit_time",
            )
        )
    )

    # Compare the keys, other than time keys, among multi-metric and
    # single metric grid search results. np.testing.assert_equal performs a
    # deep nested comparison of the two cv_results dicts
    np.testing.assert_equal(
        {k: v for k, v in cv_results_multi.items() if not k.endswith("_time")},
        {k: v for k, v in cv_results_acc_rec.items() if not k.endswith("_time")},
    )