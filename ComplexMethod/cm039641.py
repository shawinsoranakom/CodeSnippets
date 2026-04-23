def test_enet_cv_sample_weight_correctness(
    estimator, fit_intercept, sparse_container, global_random_seed
):
    """Test that ElasticNetCV with sample weights gives correct results.

    We fit the same model twice, once with weighted training data, once with repeated
    data points in the training data and check that both models converge to the
    same solution.

    Since this model uses an internal cross-validation scheme to tune the alpha
    regularization parameter, we make sure that the repetitions only occur within
    a specific CV group. Data points belonging to other CV groups stay
    unit-weighted / "unrepeated".
    """
    rng = np.random.RandomState(global_random_seed)
    n_splits, n_samples_per_cv, n_features = 3, 10, 5
    X_with_weights = rng.rand(n_splits * n_samples_per_cv, n_features)
    beta = 10 * rng.rand(n_features)
    beta[0:2] = 0
    y_with_weights = X_with_weights @ beta + rng.rand(n_splits * n_samples_per_cv)
    if issubclass(estimator, MultiTaskElasticNetCV):
        n_tasks = 3
        y_with_weights = np.tile(y_with_weights[:, None], reps=(1, n_tasks))

    if sparse_container is not None:
        X_with_weights = sparse_container(X_with_weights)
    params = dict(tol=1e-6)

    # Assign random integer weights only to the first cross-validation group.
    # The samples in the other cross-validation groups are left with unit
    # weights.

    sw = np.ones(y_with_weights.shape[0])
    sw[:n_samples_per_cv] = rng.randint(0, 5, size=n_samples_per_cv)
    groups_with_weights = np.concatenate(
        [
            np.full(n_samples_per_cv, 0),
            np.full(n_samples_per_cv, 1),
            np.full(n_samples_per_cv, 2),
        ]
    )
    splits_with_weights = list(
        LeaveOneGroupOut().split(X_with_weights, groups=groups_with_weights)
    )
    reg_with_weights = estimator(
        cv=splits_with_weights, fit_intercept=fit_intercept, **params
    )

    reg_with_weights.fit(X_with_weights, y_with_weights, sample_weight=sw)
    assert np.sum(reg_with_weights.coef_ != 0) > 1

    if sparse_container is not None:
        X_with_weights = X_with_weights.toarray()
    X_with_repetitions = np.repeat(X_with_weights, sw.astype(int), axis=0)
    if sparse_container is not None:
        X_with_repetitions = sparse_container(X_with_repetitions)

    y_with_repetitions = np.repeat(y_with_weights, sw.astype(int), axis=0)
    groups_with_repetitions = np.repeat(groups_with_weights, sw.astype(int), axis=0)

    splits_with_repetitions = list(
        LeaveOneGroupOut().split(X_with_repetitions, groups=groups_with_repetitions)
    )
    reg_with_repetitions = estimator(
        cv=splits_with_repetitions, fit_intercept=fit_intercept, **params
    )
    reg_with_repetitions.fit(X_with_repetitions, y_with_repetitions)

    # Check that the alpha selection process is the same:
    assert_allclose(reg_with_weights.mse_path_, reg_with_repetitions.mse_path_)
    assert_allclose(reg_with_weights.alphas_, reg_with_repetitions.alphas_)
    assert reg_with_weights.alpha_ == pytest.approx(reg_with_repetitions.alpha_)

    # Check that the final model coefficients are the same:
    assert_allclose(reg_with_weights.coef_, reg_with_repetitions.coef_, atol=1e-10)
    assert reg_with_weights.intercept_ == pytest.approx(reg_with_repetitions.intercept_)