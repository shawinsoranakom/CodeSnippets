def test_cv_results(Est):
    # test that the cv_results_ matches correctly the logic of the
    # tournament: in particular that the candidates continued in each
    # successive iteration are those that were best in the previous iteration
    pd = pytest.importorskip("pandas")

    rng = np.random.RandomState(0)

    n_samples = 1000
    X, y = make_classification(n_samples=n_samples, random_state=0)
    param_grid = {"a": ("l1", "l2"), "b": list(range(30))}
    base_estimator = FastClassifier()

    # generate random scores: we want to avoid ties, which would otherwise
    # mess with the ordering and make testing harder
    def scorer(est, X, y):
        return rng.rand()

    sh = Est(base_estimator, param_grid, factor=2, scoring=scorer)
    if Est is HalvingRandomSearchCV:
        # same number of candidates as with the grid
        sh.set_params(n_candidates=2 * 30, min_resources="exhaust")

    sh.fit(X, y)

    # non-regression check for
    # https://github.com/scikit-learn/scikit-learn/issues/19203
    assert isinstance(sh.cv_results_["iter"], np.ndarray)
    assert isinstance(sh.cv_results_["n_resources"], np.ndarray)

    cv_results_df = pd.DataFrame(sh.cv_results_)

    # just make sure we don't have ties
    assert len(cv_results_df["mean_test_score"].unique()) == len(cv_results_df)

    cv_results_df["params_str"] = cv_results_df["params"].apply(str)
    table = cv_results_df.pivot(
        index="params_str", columns="iter", values="mean_test_score"
    )

    # table looks like something like this:
    # iter                    0      1       2        3   4   5
    # params_str
    # {'a': 'l2', 'b': 23} 0.75    NaN     NaN      NaN NaN NaN
    # {'a': 'l1', 'b': 30} 0.90  0.875     NaN      NaN NaN NaN
    # {'a': 'l1', 'b': 0}  0.75    NaN     NaN      NaN NaN NaN
    # {'a': 'l2', 'b': 3}  0.85  0.925  0.9125  0.90625 NaN NaN
    # {'a': 'l1', 'b': 5}  0.80    NaN     NaN      NaN NaN NaN
    # ...

    # where a NaN indicates that the candidate wasn't evaluated at a given
    # iteration, because it wasn't part of the top-K at some previous
    # iteration. We here make sure that candidates that aren't in the top-k at
    # any given iteration are indeed not evaluated at the subsequent
    # iterations.
    nan_mask = pd.isna(table)
    n_iter = sh.n_iterations_
    for it in range(n_iter - 1):
        already_discarded_mask = nan_mask[it]

        # make sure that if a candidate is already discarded, we don't evaluate
        # it later
        assert (
            already_discarded_mask & nan_mask[it + 1] == already_discarded_mask
        ).all()

        # make sure that the number of discarded candidate is correct
        discarded_now_mask = ~already_discarded_mask & nan_mask[it + 1]
        kept_mask = ~already_discarded_mask & ~discarded_now_mask
        assert kept_mask.sum() == sh.n_candidates_[it + 1]

        # make sure that all discarded candidates have a lower score than the
        # kept candidates
        discarded_max_score = table[it].where(discarded_now_mask).max()
        kept_min_score = table[it].where(kept_mask).min()
        assert discarded_max_score < kept_min_score

    # We now make sure that the best candidate is chosen only from the last
    # iteration.
    # We also make sure this is true even if there were higher scores in
    # earlier rounds (this isn't generally the case, but worth ensuring it's
    # possible).

    last_iter = cv_results_df["iter"].max()
    idx_best_last_iter = cv_results_df[cv_results_df["iter"] == last_iter][
        "mean_test_score"
    ].idxmax()
    idx_best_all_iters = cv_results_df["mean_test_score"].idxmax()

    assert sh.best_params_ == cv_results_df.iloc[idx_best_last_iter]["params"]
    assert (
        cv_results_df.iloc[idx_best_last_iter]["mean_test_score"]
        < cv_results_df.iloc[idx_best_all_iters]["mean_test_score"]
    )
    assert (
        cv_results_df.iloc[idx_best_last_iter]["params"]
        != cv_results_df.iloc[idx_best_all_iters]["params"]
    )