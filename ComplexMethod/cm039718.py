def test_search_default_iid(SearchCV, specialized_params):
    # Test the IID parameter  TODO: Clearly this test does something else???
    # noise-free simple 2d-data
    X, y = make_blobs(
        centers=[[0, 0], [1, 0], [0, 1], [1, 1]],
        random_state=0,
        cluster_std=0.1,
        shuffle=False,
        n_samples=80,
    )
    # split dataset into two folds that are not iid
    # first one contains data of all 4 blobs, second only from two.
    mask = np.ones(X.shape[0], dtype=bool)
    mask[np.where(y == 1)[0][::2]] = 0
    mask[np.where(y == 2)[0][::2]] = 0
    # this leads to perfect classification on one fold and a score of 1/3 on
    # the other
    # create "cv" for splits
    cv = [[mask, ~mask], [~mask, mask]]

    common_params = {"estimator": SVC(), "cv": cv, "return_train_score": True}
    search = SearchCV(**common_params, **specialized_params)
    search.fit(X, y)

    test_cv_scores = np.array(
        [
            search.cv_results_["split%d_test_score" % s][0]
            for s in range(search.n_splits_)
        ]
    )
    test_mean = search.cv_results_["mean_test_score"][0]
    test_std = search.cv_results_["std_test_score"][0]

    train_cv_scores = np.array(
        [
            search.cv_results_["split%d_train_score" % s][0]
            for s in range(search.n_splits_)
        ]
    )
    train_mean = search.cv_results_["mean_train_score"][0]
    train_std = search.cv_results_["std_train_score"][0]

    assert search.cv_results_["param_C"][0] == 1
    # scores are the same as above
    assert_allclose(test_cv_scores, [1, 1.0 / 3.0])
    assert_allclose(train_cv_scores, [1, 1])
    # Unweighted mean/std is used
    assert test_mean == pytest.approx(np.mean(test_cv_scores))
    assert test_std == pytest.approx(np.std(test_cv_scores))

    # For the train scores, we do not take a weighted mean irrespective of
    # i.i.d. or not
    assert train_mean == pytest.approx(1)
    assert train_std == pytest.approx(0)