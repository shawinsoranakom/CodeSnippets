def test_sgd_proba(klass):
    # Check SGD.predict_proba

    # Hinge loss does not allow for conditional prob estimate.
    # We cannot use the factory here, because it defines predict_proba
    # anyway.
    clf = SGDClassifier(loss="hinge", alpha=0.01, max_iter=10, tol=None).fit(X, Y)
    assert not hasattr(clf, "predict_proba")
    assert not hasattr(clf, "predict_log_proba")

    # log and modified_huber losses can output probability estimates
    # binary case
    for loss in ["log_loss", "modified_huber"]:
        clf = klass(loss=loss, alpha=0.01, max_iter=10)
        clf.fit(X, Y)
        p = clf.predict_proba([[3, 2]])
        assert p[0, 1] > 0.5
        p = clf.predict_proba([[-1, -1]])
        assert p[0, 1] < 0.5

        # If predict_proba is 0, we get "RuntimeWarning: divide by zero encountered
        # in log". We avoid it here.
        with np.errstate(divide="ignore"):
            p = clf.predict_log_proba([[3, 2]])
            assert p[0, 1] > p[0, 0]
            p = clf.predict_log_proba([[-1, -1]])
            assert p[0, 1] < p[0, 0]

    # log loss multiclass probability estimates
    clf = klass(loss="log_loss", alpha=0.01, max_iter=10).fit(X2, Y2)

    d = clf.decision_function([[0.1, -0.1], [0.3, 0.2]])
    p = clf.predict_proba([[0.1, -0.1], [0.3, 0.2]])
    assert_array_equal(np.argmax(p, axis=1), np.argmax(d, axis=1))
    assert_almost_equal(p[0].sum(), 1)
    assert np.all(p[0] >= 0)

    p = clf.predict_proba([[-1, -1]])
    d = clf.decision_function([[-1, -1]])
    assert_array_equal(np.argsort(p[0]), np.argsort(d[0]))

    lp = clf.predict_log_proba([[3, 2]])
    p = clf.predict_proba([[3, 2]])
    assert_array_almost_equal(np.log(p), lp)

    lp = clf.predict_log_proba([[-1, -1]])
    p = clf.predict_proba([[-1, -1]])
    assert_array_almost_equal(np.log(p), lp)

    # Modified Huber multiclass probability estimates; requires a separate
    # test because the hard zero/one probabilities may destroy the
    # ordering present in decision_function output.
    clf = klass(loss="modified_huber", alpha=0.01, max_iter=10)
    clf.fit(X2, Y2)
    d = clf.decision_function([[3, 2]])
    p = clf.predict_proba([[3, 2]])
    if klass != SparseSGDClassifier:
        assert np.argmax(d, axis=1) == np.argmax(p, axis=1)
    else:  # XXX the sparse test gets a different X2 (?)
        assert np.argmin(d, axis=1) == np.argmin(p, axis=1)

    # the following sample produces decision_function values < -1,
    # which would cause naive normalization to fail (see comment
    # in SGDClassifier.predict_proba)
    x = X.mean(axis=0)
    d = clf.decision_function([x])
    if np.all(d < -1):  # XXX not true in sparse test case (why?)
        p = clf.predict_proba([x])
        assert_array_almost_equal(p[0], [1 / 3.0] * 3)