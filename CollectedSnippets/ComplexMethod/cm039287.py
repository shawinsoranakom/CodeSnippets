def test_multi_output_delegate_predict_proba():
    """Check the behavior for the delegation of predict_proba to the underlying
    estimator"""

    # A base estimator with `predict_proba`should expose the method even before fit
    moc = MultiOutputClassifier(LogisticRegression())
    assert hasattr(moc, "predict_proba")
    moc.fit(X, y)
    assert hasattr(moc, "predict_proba")

    # A base estimator without `predict_proba` should raise an AttributeError
    moc = MultiOutputClassifier(LinearSVC())
    assert not hasattr(moc, "predict_proba")

    outer_msg = "'MultiOutputClassifier' has no attribute 'predict_proba'"
    inner_msg = "'LinearSVC' object has no attribute 'predict_proba'"
    with pytest.raises(AttributeError, match=outer_msg) as exec_info:
        moc.predict_proba(X)
    assert isinstance(exec_info.value.__cause__, AttributeError)
    assert inner_msg == str(exec_info.value.__cause__)

    moc.fit(X, y)
    assert not hasattr(moc, "predict_proba")
    with pytest.raises(AttributeError, match=outer_msg) as exec_info:
        moc.predict_proba(X)
    assert isinstance(exec_info.value.__cause__, AttributeError)
    assert inner_msg == str(exec_info.value.__cause__)