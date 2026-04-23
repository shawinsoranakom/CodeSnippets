def test_same_predictions_multiclass_classification(
    seed, min_samples_leaf, n_samples, max_leaf_nodes
):
    # Same as test_same_predictions_regression but for classification
    pytest.importorskip("lightgbm")

    rng = np.random.RandomState(seed=seed)
    n_classes = 3
    max_iter = 1
    max_bins = 255
    lr = 1

    X, y = make_classification(
        n_samples=n_samples,
        n_classes=n_classes,
        n_features=5,
        n_informative=5,
        n_redundant=0,
        n_clusters_per_class=1,
        random_state=0,
    )

    if n_samples > 255:
        # bin data and convert it to float32 so that the estimator doesn't
        # treat it as pre-binned
        X = _BinMapper(n_bins=max_bins + 1).fit_transform(X).astype(np.float32)

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=rng)

    est_sklearn = HistGradientBoostingClassifier(
        loss="log_loss",
        max_iter=max_iter,
        max_bins=max_bins,
        learning_rate=lr,
        early_stopping=False,
        min_samples_leaf=min_samples_leaf,
        max_leaf_nodes=max_leaf_nodes,
    )
    est_lightgbm = get_equivalent_estimator(
        est_sklearn, lib="lightgbm", n_classes=n_classes
    )

    est_lightgbm.fit(X_train, y_train)
    est_sklearn.fit(X_train, y_train)

    # We need X to be treated a numerical data, not pre-binned data.
    X_train, X_test = X_train.astype(np.float32), X_test.astype(np.float32)

    pred_lightgbm = est_lightgbm.predict(X_train)
    pred_sklearn = est_sklearn.predict(X_train)
    assert np.mean(pred_sklearn == pred_lightgbm) > 0.89

    proba_lightgbm = est_lightgbm.predict_proba(X_train)
    proba_sklearn = est_sklearn.predict_proba(X_train)
    # assert more than 75% of the predicted probabilities are the same up to
    # the second decimal
    assert np.mean(np.abs(proba_lightgbm - proba_sklearn) < 1e-2) > 0.75

    acc_lightgbm = accuracy_score(y_train, pred_lightgbm)
    acc_sklearn = accuracy_score(y_train, pred_sklearn)

    np.testing.assert_allclose(acc_lightgbm, acc_sklearn, rtol=0, atol=5e-2)

    if max_leaf_nodes < 10 and n_samples >= 1000:
        pred_lightgbm = est_lightgbm.predict(X_test)
        pred_sklearn = est_sklearn.predict(X_test)
        assert np.mean(pred_sklearn == pred_lightgbm) > 0.89

        proba_lightgbm = est_lightgbm.predict_proba(X_train)
        proba_sklearn = est_sklearn.predict_proba(X_train)
        # assert more than 75% of the predicted probabilities are the same up
        # to the second decimal
        assert np.mean(np.abs(proba_lightgbm - proba_sklearn) < 1e-2) > 0.75

        acc_lightgbm = accuracy_score(y_test, pred_lightgbm)
        acc_sklearn = accuracy_score(y_test, pred_sklearn)
        np.testing.assert_almost_equal(acc_lightgbm, acc_sklearn, decimal=2)