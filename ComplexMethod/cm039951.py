def test_check_is_fitted_attributes():
    class MyEstimator(BaseEstimator):
        def fit(self, X, y):
            return self

    msg = "not fitted"
    est = MyEstimator()

    assert not _is_fitted(est, attributes=["a_", "b_"])
    with pytest.raises(NotFittedError, match=msg):
        check_is_fitted(est, attributes=["a_", "b_"])
    assert not _is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    with pytest.raises(NotFittedError, match=msg):
        check_is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    assert not _is_fitted(est, attributes=["a_", "b_"], all_or_any=any)
    with pytest.raises(NotFittedError, match=msg):
        check_is_fitted(est, attributes=["a_", "b_"], all_or_any=any)

    est.a_ = "a"
    assert not _is_fitted(est, attributes=["a_", "b_"])
    with pytest.raises(NotFittedError, match=msg):
        check_is_fitted(est, attributes=["a_", "b_"])
    assert not _is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    with pytest.raises(NotFittedError, match=msg):
        check_is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    assert _is_fitted(est, attributes=["a_", "b_"], all_or_any=any)
    check_is_fitted(est, attributes=["a_", "b_"], all_or_any=any)

    est.b_ = "b"
    assert _is_fitted(est, attributes=["a_", "b_"])
    check_is_fitted(est, attributes=["a_", "b_"])
    assert _is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    check_is_fitted(est, attributes=["a_", "b_"], all_or_any=all)
    assert _is_fitted(est, attributes=["a_", "b_"], all_or_any=any)
    check_is_fitted(est, attributes=["a_", "b_"], all_or_any=any)