def test_grid_search_cv_splits_consistency():
    # Check if a one time iterable is accepted as a cv parameter.
    n_samples = 100
    n_splits = 5
    X, y = make_classification(n_samples=n_samples, random_state=0)

    gs = GridSearchCV(
        LinearSVC(random_state=0),
        param_grid={"C": [0.1, 0.2, 0.3]},
        cv=OneTimeSplitter(n_splits=n_splits, n_samples=n_samples),
        return_train_score=True,
    )
    gs.fit(X, y)

    gs2 = GridSearchCV(
        LinearSVC(random_state=0),
        param_grid={"C": [0.1, 0.2, 0.3]},
        cv=KFold(n_splits=n_splits),
        return_train_score=True,
    )
    gs2.fit(X, y)

    # Give generator as a cv parameter
    assert isinstance(
        KFold(n_splits=n_splits, shuffle=True, random_state=0).split(X, y),
        GeneratorType,
    )
    gs3 = GridSearchCV(
        LinearSVC(random_state=0),
        param_grid={"C": [0.1, 0.2, 0.3]},
        cv=KFold(n_splits=n_splits, shuffle=True, random_state=0).split(X, y),
        return_train_score=True,
    )
    gs3.fit(X, y)

    gs4 = GridSearchCV(
        LinearSVC(random_state=0),
        param_grid={"C": [0.1, 0.2, 0.3]},
        cv=KFold(n_splits=n_splits, shuffle=True, random_state=0),
        return_train_score=True,
    )
    gs4.fit(X, y)

    def _pop_time_keys(cv_results):
        for key in (
            "mean_fit_time",
            "std_fit_time",
            "mean_score_time",
            "std_score_time",
        ):
            cv_results.pop(key)
        return cv_results

    # Check if generators are supported as cv and
    # that the splits are consistent
    np.testing.assert_equal(
        _pop_time_keys(gs3.cv_results_), _pop_time_keys(gs4.cv_results_)
    )

    # OneTimeSplitter is a non-re-entrant cv where split can be called only
    # once if ``cv.split`` is called once per param setting in GridSearchCV.fit
    # the 2nd and 3rd parameter will not be evaluated as no train/test indices
    # will be generated for the 2nd and subsequent cv.split calls.
    # This is a check to make sure cv.split is not called once per param
    # setting.
    np.testing.assert_equal(
        {k: v for k, v in gs.cv_results_.items() if not k.endswith("_time")},
        {k: v for k, v in gs2.cv_results_.items() if not k.endswith("_time")},
    )

    # Check consistency of folds across the parameters
    gs = GridSearchCV(
        LinearSVC(random_state=0),
        param_grid={"C": [0.1, 0.1, 0.2, 0.2]},
        cv=KFold(n_splits=n_splits, shuffle=True),
        return_train_score=True,
    )
    gs.fit(X, y)

    # As the first two param settings (C=0.1) and the next two param
    # settings (C=0.2) are same, the test and train scores must also be
    # same as long as the same train/test indices are generated for all
    # the cv splits, for both param setting
    for score_type in ("train", "test"):
        per_param_scores = {}
        for param_i in range(4):
            per_param_scores[param_i] = [
                gs.cv_results_["split%d_%s_score" % (s, score_type)][param_i]
                for s in range(5)
            ]

        assert_array_almost_equal(per_param_scores[0], per_param_scores[1])
        assert_array_almost_equal(per_param_scores[2], per_param_scores[3])