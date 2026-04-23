def test_staged_predict():
    # Check staged predictions.
    rng = np.random.RandomState(0)
    iris_weights = rng.randint(10, size=iris.target.shape)
    diabetes_weights = rng.randint(10, size=diabetes.target.shape)

    clf = AdaBoostClassifier(n_estimators=10)
    clf.fit(iris.data, iris.target, sample_weight=iris_weights)

    predictions = clf.predict(iris.data)
    staged_predictions = [p for p in clf.staged_predict(iris.data)]
    proba = clf.predict_proba(iris.data)
    staged_probas = [p for p in clf.staged_predict_proba(iris.data)]
    score = clf.score(iris.data, iris.target, sample_weight=iris_weights)
    staged_scores = [
        s for s in clf.staged_score(iris.data, iris.target, sample_weight=iris_weights)
    ]

    assert len(staged_predictions) == 10
    assert_array_almost_equal(predictions, staged_predictions[-1])
    assert len(staged_probas) == 10
    assert_array_almost_equal(proba, staged_probas[-1])
    assert len(staged_scores) == 10
    assert_array_almost_equal(score, staged_scores[-1])

    # AdaBoost regression
    clf = AdaBoostRegressor(n_estimators=10, random_state=0)
    clf.fit(diabetes.data, diabetes.target, sample_weight=diabetes_weights)

    predictions = clf.predict(diabetes.data)
    staged_predictions = [p for p in clf.staged_predict(diabetes.data)]
    score = clf.score(diabetes.data, diabetes.target, sample_weight=diabetes_weights)
    staged_scores = [
        s
        for s in clf.staged_score(
            diabetes.data, diabetes.target, sample_weight=diabetes_weights
        )
    ]

    assert len(staged_predictions) == 10
    assert_array_almost_equal(predictions, staged_predictions[-1])
    assert len(staged_scores) == 10
    assert_array_almost_equal(score, staged_scores[-1])