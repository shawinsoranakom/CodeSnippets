def test_search_cv_timing():
    svc = LinearSVC(random_state=0)

    X = [
        [
            1,
        ],
        [
            2,
        ],
        [
            3,
        ],
        [
            4,
        ],
    ]
    y = [0, 1, 1, 0]

    gs = GridSearchCV(svc, {"C": [0, 1]}, cv=2, error_score=0)
    rs = RandomizedSearchCV(svc, {"C": [0, 1]}, cv=2, error_score=0, n_iter=2)

    for search in (gs, rs):
        search.fit(X, y)
        for key in ["mean_fit_time", "std_fit_time"]:
            # NOTE The precision of time.time in windows is not high
            # enough for the fit/score times to be non-zero for trivial X and y
            assert np.all(search.cv_results_[key] >= 0)
            assert np.all(search.cv_results_[key] < 1)

        for key in ["mean_score_time", "std_score_time"]:
            assert search.cv_results_[key][1] >= 0
            assert search.cv_results_[key][0] == 0.0
            assert np.all(search.cv_results_[key] < 1)

        assert hasattr(search, "refit_time_")
        assert isinstance(search.refit_time_, float)
        assert search.refit_time_ >= 0