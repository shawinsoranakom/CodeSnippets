def test_classification_scorer_sample_weight():
    # Test that classification scorers support sample_weight or raise sensible
    # errors

    # Unlike the metrics invariance test, in the scorer case it's harder
    # to ensure that, on the classifier output, weighted and unweighted
    # scores really should be unequal.
    X, y = make_classification(random_state=0)
    _, y_ml = make_multilabel_classification(n_samples=X.shape[0], random_state=0)
    split = train_test_split(X, y, y_ml, random_state=0)
    X_train, X_test, y_train, y_test, y_ml_train, y_ml_test = split

    sample_weight = np.ones_like(y_test)
    sample_weight[:10] = 0

    # get sensible estimators for each metric
    estimator = _make_estimators(X_train, y_train, y_ml_train)

    for name in get_scorer_names():
        scorer = get_scorer(name)
        if name in REGRESSION_SCORERS:
            # skip the regression scores
            continue
        if name == "top_k_accuracy":
            # in the binary case k > 1 will always lead to a perfect score
            scorer._kwargs = {"k": 1}
        if name in MULTILABEL_ONLY_SCORERS:
            target = y_ml_test
        else:
            target = y_test
        try:
            weighted = scorer(
                estimator[name], X_test, target, sample_weight=sample_weight
            )
            ignored = scorer(estimator[name], X_test[10:], target[10:])
            unweighted = scorer(estimator[name], X_test, target)
            # this should not raise. sample_weight should be ignored if None.
            _ = scorer(estimator[name], X_test[:10], target[:10], sample_weight=None)
            assert weighted != unweighted, (
                f"scorer {name} behaves identically when called with "
                f"sample weights: {weighted} vs {unweighted}"
            )
            assert_almost_equal(
                weighted,
                ignored,
                err_msg=(
                    f"scorer {name} behaves differently "
                    "when ignoring samples and setting "
                    f"sample_weight to 0: {weighted} vs {ignored}"
                ),
            )

        except TypeError as e:
            assert "sample_weight" in str(e), (
                f"scorer {name} raises unhelpful exception when called "
                f"with sample weights: {e}"
            )