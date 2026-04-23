def check_svm_model_equal(dense_svm, X_train, y_train, X_test):
    # Use the original svm model for dense fit and clone an exactly same
    # svm model for sparse fit
    sparse_svm = base.clone(dense_svm)

    dense_svm.fit(X_train.toarray(), y_train)
    if sparse.issparse(X_test):
        X_test_dense = X_test.toarray()
    else:
        X_test_dense = X_test
    sparse_svm.fit(X_train, y_train)
    assert sparse.issparse(sparse_svm.support_vectors_)
    assert sparse.issparse(sparse_svm.dual_coef_)
    assert_allclose(dense_svm.support_vectors_, sparse_svm.support_vectors_.toarray())
    assert_allclose(dense_svm.dual_coef_, sparse_svm.dual_coef_.toarray())
    if dense_svm.kernel == "linear":
        assert sparse.issparse(sparse_svm.coef_)
        assert_array_almost_equal(dense_svm.coef_, sparse_svm.coef_.toarray())
    assert_allclose(dense_svm.support_, sparse_svm.support_)
    assert_allclose(dense_svm.predict(X_test_dense), sparse_svm.predict(X_test))

    assert_array_almost_equal(
        dense_svm.decision_function(X_test_dense), sparse_svm.decision_function(X_test)
    )
    assert_array_almost_equal(
        dense_svm.decision_function(X_test_dense),
        sparse_svm.decision_function(X_test_dense),
    )
    if isinstance(dense_svm, svm.OneClassSVM):
        msg = "cannot use sparse input in 'OneClassSVM' trained on dense data"
    else:
        if hasattr(dense_svm, "predict_proba"):
            assert_array_almost_equal(
                dense_svm.predict_proba(X_test_dense),
                sparse_svm.predict_proba(X_test),
                decimal=4,
            )
        msg = "cannot use sparse input in 'SVC' trained on dense data"
    if sparse.issparse(X_test):
        with pytest.raises(ValueError, match=msg):
            dense_svm.predict(X_test)