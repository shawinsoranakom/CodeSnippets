def test_KNeighborsClassifier_multioutput():
    # Test k-NN classifier on multioutput data
    rng = check_random_state(0)
    n_features = 5
    n_samples = 50
    n_output = 3

    X = rng.rand(n_samples, n_features)
    y = rng.randint(0, 3, (n_samples, n_output))

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

    weights = [None, "uniform", "distance", _weight_func]

    for algorithm, weights in product(ALGORITHMS, weights):
        # Stack single output prediction
        y_pred_so = []
        y_pred_proba_so = []
        for o in range(n_output):
            knn = neighbors.KNeighborsClassifier(weights=weights, algorithm=algorithm)
            knn.fit(X_train, y_train[:, o])
            y_pred_so.append(knn.predict(X_test))
            y_pred_proba_so.append(knn.predict_proba(X_test))

        y_pred_so = np.vstack(y_pred_so).T
        assert y_pred_so.shape == y_test.shape
        assert len(y_pred_proba_so) == n_output

        # Multioutput prediction
        knn_mo = neighbors.KNeighborsClassifier(weights=weights, algorithm=algorithm)
        knn_mo.fit(X_train, y_train)
        y_pred_mo = knn_mo.predict(X_test)

        assert y_pred_mo.shape == y_test.shape
        assert_array_equal(y_pred_mo, y_pred_so)

        # Check proba
        y_pred_proba_mo = knn_mo.predict_proba(X_test)
        assert len(y_pred_proba_mo) == n_output

        for proba_mo, proba_so in zip(y_pred_proba_mo, y_pred_proba_so):
            assert_array_equal(proba_mo, proba_so)