def test_plain_has_no_average_attr(klass):
    clf = klass(average=True, eta0=0.01)
    clf.fit(X, Y)

    assert hasattr(clf, "_average_coef")
    assert hasattr(clf, "_average_intercept")
    assert hasattr(clf, "_standard_intercept")
    assert hasattr(clf, "_standard_coef")

    clf = klass()
    clf.fit(X, Y)

    assert not hasattr(clf, "_average_coef")
    assert not hasattr(clf, "_average_intercept")
    assert not hasattr(clf, "_standard_intercept")
    assert not hasattr(clf, "_standard_coef")