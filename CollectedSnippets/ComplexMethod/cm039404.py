def test_hasattr_prediction():
    # check availability of prediction methods depending on novelty value.
    X = [[1, 1], [1, 2], [2, 1]]

    # when novelty=True
    clf = neighbors.LocalOutlierFactor(novelty=True)
    clf.fit(X)
    assert hasattr(clf, "predict")
    assert hasattr(clf, "decision_function")
    assert hasattr(clf, "score_samples")
    assert not hasattr(clf, "fit_predict")

    # when novelty=False
    clf = neighbors.LocalOutlierFactor(novelty=False)
    clf.fit(X)
    assert hasattr(clf, "fit_predict")
    assert not hasattr(clf, "predict")
    assert not hasattr(clf, "decision_function")
    assert not hasattr(clf, "score_samples")