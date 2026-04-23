def test_classifier_partial_fit(csr_container, average):
    classes = np.unique(y)
    data = csr_container(X) if csr_container is not None else X
    clf = PassiveAggressiveClassifier(random_state=0, average=average, max_iter=5)
    for t in range(30):
        clf.partial_fit(data, y, classes)
    score = clf.score(data, y)
    assert score > 0.79
    if average:
        assert hasattr(clf, "_average_coef")
        assert hasattr(clf, "_average_intercept")
        assert hasattr(clf, "_standard_intercept")
        assert hasattr(clf, "_standard_coef")