def test_iterative_imputer_imputation_order(imputation_order):
    rng = np.random.RandomState(0)
    n = 100
    d = 10
    max_iter = 2
    X = _sparse_random_matrix(n, d, density=0.10, random_state=rng).toarray()
    X[:, 0] = 1  # this column should not be discarded by IterativeImputer

    imputer = IterativeImputer(
        missing_values=0,
        max_iter=max_iter,
        n_nearest_features=5,
        sample_posterior=False,
        skip_complete=True,
        min_value=0,
        max_value=1,
        verbose=1,
        imputation_order=imputation_order,
        random_state=rng,
    )
    imputer.fit_transform(X)
    ordered_idx = [i.feat_idx for i in imputer.imputation_sequence_]

    assert len(ordered_idx) // imputer.n_iter_ == imputer.n_features_with_missing_

    if imputation_order == "roman":
        assert np.all(ordered_idx[: d - 1] == np.arange(1, d))
    elif imputation_order == "arabic":
        assert np.all(ordered_idx[: d - 1] == np.arange(d - 1, 0, -1))
    elif imputation_order == "random":
        ordered_idx_round_1 = ordered_idx[: d - 1]
        ordered_idx_round_2 = ordered_idx[d - 1 :]
        assert ordered_idx_round_1 != ordered_idx_round_2
    elif "ending" in imputation_order:
        assert len(ordered_idx) == max_iter * (d - 1)