def test_ensemble_heterogeneous_estimators_behavior(X, y, estimator):
    # check that the behavior of `estimators`, `estimators_`,
    # `named_estimators`, `named_estimators_` is consistent across all
    # ensemble classes and when using `set_params()`.
    estimator = clone(estimator)  # Avoid side effects from shared instances

    # before fit
    assert "svm" in estimator.named_estimators
    assert estimator.named_estimators.svm is estimator.estimators[1][1]
    assert estimator.named_estimators.svm is estimator.named_estimators["svm"]

    # check fitted attributes
    estimator.fit(X, y)
    assert len(estimator.named_estimators) == 3
    assert len(estimator.named_estimators_) == 3
    assert sorted(list(estimator.named_estimators_.keys())) == sorted(
        ["lr", "svm", "rf"]
    )

    # check that set_params() does not add a new attribute
    estimator_new_params = clone(estimator)
    svm_estimator = SVC() if is_classifier(estimator) else SVR()
    estimator_new_params.set_params(svm=svm_estimator).fit(X, y)
    assert not hasattr(estimator_new_params, "svm")
    assert (
        estimator_new_params.named_estimators.lr.get_params()
        == estimator.named_estimators.lr.get_params()
    )
    assert (
        estimator_new_params.named_estimators.rf.get_params()
        == estimator.named_estimators.rf.get_params()
    )

    # check the behavior when setting and dropping an estimator
    estimator_dropped = clone(estimator)
    estimator_dropped.set_params(svm="drop")
    estimator_dropped.fit(X, y)
    assert len(estimator_dropped.named_estimators) == 3
    assert estimator_dropped.named_estimators.svm == "drop"
    assert len(estimator_dropped.named_estimators_) == 3
    assert sorted(list(estimator_dropped.named_estimators_.keys())) == sorted(
        ["lr", "svm", "rf"]
    )
    for sub_est in estimator_dropped.named_estimators_:
        # check that the correspondence is correct
        assert not isinstance(sub_est, type(estimator.named_estimators.svm))

    # check that we can set the parameters of the underlying classifier
    estimator.set_params(svm__C=10.0)
    estimator.set_params(rf__max_depth=5)
    assert (
        estimator.get_params()["svm__C"]
        == estimator.get_params()["svm"].get_params()["C"]
    )
    assert (
        estimator.get_params()["rf__max_depth"]
        == estimator.get_params()["rf"].get_params()["max_depth"]
    )