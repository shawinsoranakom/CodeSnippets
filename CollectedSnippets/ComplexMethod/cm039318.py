def test_pairwise_n_features_in():
    """Check the n_features_in_ attributes of the meta and base estimators

    When the training data is a regular design matrix, everything is intuitive.
    However, when the training data is a precomputed kernel matrix, the
    multiclass strategy can resample the kernel matrix of the underlying base
    estimator both row-wise and column-wise and this has a non-trivial impact
    on the expected value for the n_features_in_ of both the meta and the base
    estimators.
    """
    X, y = iris.data, iris.target

    # Remove the last sample to make the classes not exactly balanced and make
    # the test more interesting.
    assert y[-1] == 0
    X = X[:-1]
    y = y[:-1]

    # Fitting directly on the design matrix:
    assert X.shape == (149, 4)

    clf_notprecomputed = svm.SVC(kernel="linear").fit(X, y)
    assert clf_notprecomputed.n_features_in_ == 4

    ovr_notprecomputed = OneVsRestClassifier(clf_notprecomputed).fit(X, y)
    assert ovr_notprecomputed.n_features_in_ == 4
    for est in ovr_notprecomputed.estimators_:
        assert est.n_features_in_ == 4

    ovo_notprecomputed = OneVsOneClassifier(clf_notprecomputed).fit(X, y)
    assert ovo_notprecomputed.n_features_in_ == 4
    assert ovo_notprecomputed.n_classes_ == 3
    assert len(ovo_notprecomputed.estimators_) == 3
    for est in ovo_notprecomputed.estimators_:
        assert est.n_features_in_ == 4

    # When working with precomputed kernels we have one "feature" per training
    # sample:
    K = X @ X.T
    assert K.shape == (149, 149)

    clf_precomputed = svm.SVC(kernel="precomputed").fit(K, y)
    assert clf_precomputed.n_features_in_ == 149

    ovr_precomputed = OneVsRestClassifier(clf_precomputed).fit(K, y)
    assert ovr_precomputed.n_features_in_ == 149
    assert ovr_precomputed.n_classes_ == 3
    assert len(ovr_precomputed.estimators_) == 3
    for est in ovr_precomputed.estimators_:
        assert est.n_features_in_ == 149

    # This becomes really interesting with OvO and precomputed kernel together:
    # internally, OvO will drop the samples of the classes not part of the pair
    # of classes under consideration for a given binary classifier. Since we
    # use a precomputed kernel, it will also drop the matching columns of the
    # kernel matrix, and therefore we have fewer "features" as result.
    #
    # Since class 0 has 49 samples, and class 1 and 2 have 50 samples each, a
    # single OvO binary classifier works with a sub-kernel matrix of shape
    # either (99, 99) or (100, 100).
    ovo_precomputed = OneVsOneClassifier(clf_precomputed).fit(K, y)
    assert ovo_precomputed.n_features_in_ == 149
    assert ovr_precomputed.n_classes_ == 3
    assert len(ovr_precomputed.estimators_) == 3
    assert ovo_precomputed.estimators_[0].n_features_in_ == 99  # class 0 vs class 1
    assert ovo_precomputed.estimators_[1].n_features_in_ == 99  # class 0 vs class 2
    assert ovo_precomputed.estimators_[2].n_features_in_ == 100