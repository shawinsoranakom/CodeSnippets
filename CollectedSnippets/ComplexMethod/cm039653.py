def test_ridge_gcv_sample_weights(
    gcv_mode, X_container, fit_intercept, n_features, y_shape, noise
):
    if gcv_mode == "svd" and (X_container in CSR_CONTAINERS):
        pytest.skip("`svd` mode not supported for sparse X.")
    alphas = [1e-3, 0.1, 1.0, 10.0, 1e3]
    rng = np.random.RandomState(0)
    n_targets = y_shape[-1] if len(y_shape) == 2 else 1
    X, y = _make_sparse_offset_regression(
        n_samples=11,
        n_features=n_features,
        n_targets=n_targets,
        random_state=0,
        shuffle=False,
        noise=noise,
    )
    y = y.reshape(y_shape)

    sample_weight = 3 * rng.randn(len(X))
    sample_weight = (sample_weight - sample_weight.min() + 1).astype(int)
    indices = np.repeat(np.arange(X.shape[0]), sample_weight)
    sample_weight = sample_weight.astype(float)
    X_tiled, y_tiled = X[indices], y[indices]

    cv = GroupKFold(n_splits=X.shape[0])
    splits = cv.split(X_tiled, y_tiled, groups=indices)
    kfold = RidgeCV(
        alphas=alphas,
        cv=splits,
        scoring="neg_mean_squared_error",
        fit_intercept=fit_intercept,
    )
    kfold.fit(X_tiled, y_tiled)

    ridge_reg = Ridge(alpha=kfold.alpha_, fit_intercept=fit_intercept)
    splits = cv.split(X_tiled, y_tiled, groups=indices)
    predictions = cross_val_predict(ridge_reg, X_tiled, y_tiled, cv=splits)
    if predictions.shape != y_tiled.shape:
        predictions = predictions.reshape(y_tiled.shape)
    kfold_errors = (y_tiled - predictions) ** 2
    kfold_errors = [
        np.sum(kfold_errors[indices == i], axis=0) for i in np.arange(X.shape[0])
    ]
    kfold_errors = np.asarray(kfold_errors)

    X_gcv = X_container(X)
    gcv_ridge = RidgeCV(
        alphas=alphas,
        store_cv_results=True,
        gcv_mode=gcv_mode,
        fit_intercept=fit_intercept,
    )
    gcv_ridge.fit(X_gcv, y, sample_weight=sample_weight)
    if len(y_shape) == 2:
        gcv_errors = gcv_ridge.cv_results_[:, :, alphas.index(kfold.alpha_)]
    else:
        gcv_errors = gcv_ridge.cv_results_[:, alphas.index(kfold.alpha_)]

    assert kfold.alpha_ == pytest.approx(gcv_ridge.alpha_)
    assert_allclose(gcv_errors, kfold_errors, rtol=1e-3)
    assert_allclose(gcv_ridge.coef_, kfold.coef_, rtol=1e-3)
    assert_allclose(gcv_ridge.intercept_, kfold.intercept_, rtol=1e-3)