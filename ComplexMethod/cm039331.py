def test_rfecv(csr_container):
    generator = check_random_state(0)
    iris = load_iris()
    # Add some irrelevant features. Random seed is set to make sure that
    # irrelevant features are always irrelevant.
    X = np.c_[iris.data, generator.normal(size=(len(iris.data), 6))]
    y = list(iris.target)  # regression test: list should be supported

    # Test using the score function
    rfecv = RFECV(estimator=SVC(kernel="linear"), step=1)
    rfecv.fit(X, y)
    # non-regression test for missing worst feature:

    for key in rfecv.cv_results_.keys():
        assert len(rfecv.cv_results_[key]) == X.shape[1]

    assert len(rfecv.ranking_) == X.shape[1]
    X_r = rfecv.transform(X)

    # All the noisy variable were filtered out
    assert_array_equal(X_r, iris.data)

    # same in sparse
    rfecv_sparse = RFECV(estimator=SVC(kernel="linear"), step=1)
    X_sparse = csr_container(X)
    rfecv_sparse.fit(X_sparse, y)
    X_r_sparse = rfecv_sparse.transform(X_sparse)
    assert_array_equal(X_r_sparse.toarray(), iris.data)

    # Test using a customized loss function
    scoring = make_scorer(zero_one_loss, greater_is_better=False)
    rfecv = RFECV(estimator=SVC(kernel="linear"), step=1, scoring=scoring)
    ignore_warnings(rfecv.fit)(X, y)
    X_r = rfecv.transform(X)
    assert_array_equal(X_r, iris.data)

    # Test using a scorer
    scorer = get_scorer("accuracy")
    rfecv = RFECV(estimator=SVC(kernel="linear"), step=1, scoring=scorer)
    rfecv.fit(X, y)
    X_r = rfecv.transform(X)
    assert_array_equal(X_r, iris.data)

    # Test fix on cv_results_
    def test_scorer(estimator, X, y):
        return 1.0

    rfecv = RFECV(estimator=SVC(kernel="linear"), step=1, scoring=test_scorer)
    rfecv.fit(X, y)

    # In the event of cross validation score ties, the expected behavior of
    # RFECV is to return the FEWEST features that maximize the CV score.
    # Because test_scorer always returns 1.0 in this example, RFECV should
    # reduce the dimensionality to a single feature (i.e. n_features_ = 1)
    assert rfecv.n_features_ == 1

    # Same as the first two tests, but with step=2
    rfecv = RFECV(estimator=SVC(kernel="linear"), step=2)
    rfecv.fit(X, y)

    for key in rfecv.cv_results_.keys():
        assert len(rfecv.cv_results_[key]) == 6

    assert len(rfecv.ranking_) == X.shape[1]
    X_r = rfecv.transform(X)
    assert_array_equal(X_r, iris.data)

    rfecv_sparse = RFECV(estimator=SVC(kernel="linear"), step=2)
    X_sparse = csr_container(X)
    rfecv_sparse.fit(X_sparse, y)
    X_r_sparse = rfecv_sparse.transform(X_sparse)
    assert_array_equal(X_r_sparse.toarray(), iris.data)

    # Verifying that steps < 1 don't blow up.
    rfecv_sparse = RFECV(estimator=SVC(kernel="linear"), step=0.2)
    X_sparse = csr_container(X)
    rfecv_sparse.fit(X_sparse, y)
    X_r_sparse = rfecv_sparse.transform(X_sparse)
    assert_array_equal(X_r_sparse.toarray(), iris.data)