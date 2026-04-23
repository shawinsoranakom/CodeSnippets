def check_classifier_multioutput(name, estimator_orig):
    n_samples, n_labels, n_classes = 42, 5, 3
    tags = get_tags(estimator_orig)
    estimator = clone(estimator_orig)
    X, y = make_multilabel_classification(
        random_state=42, n_samples=n_samples, n_labels=n_labels, n_classes=n_classes
    )
    X = _enforce_estimator_tags_X(estimator, X)
    estimator.fit(X, y)
    y_pred = estimator.predict(X)

    assert y_pred.shape == (n_samples, n_classes), (
        "The shape of the prediction for multioutput data is "
        "incorrect. Expected {}, got {}.".format((n_samples, n_labels), y_pred.shape)
    )
    assert y_pred.dtype.kind == "i"

    if hasattr(estimator, "decision_function"):
        decision = estimator.decision_function(X)
        assert isinstance(decision, np.ndarray)
        assert decision.shape == (n_samples, n_classes), (
            "The shape of the decision function output for "
            "multioutput data is incorrect. Expected {}, got {}.".format(
                (n_samples, n_classes), decision.shape
            )
        )

        dec_pred = (decision > 0).astype(int)
        dec_exp = estimator.classes_[dec_pred]
        assert_array_equal(dec_exp, y_pred)

    if hasattr(estimator, "predict_proba"):
        y_prob = estimator.predict_proba(X)

        if isinstance(y_prob, list) and not tags.classifier_tags.poor_score:
            for i in range(n_classes):
                assert y_prob[i].shape == (n_samples, 2), (
                    "The shape of the probability for multioutput data is"
                    " incorrect. Expected {}, got {}.".format(
                        (n_samples, 2), y_prob[i].shape
                    )
                )
                assert_array_equal(
                    np.argmax(y_prob[i], axis=1).astype(int), y_pred[:, i]
                )
        elif not tags.classifier_tags.poor_score:
            assert y_prob.shape == (n_samples, n_classes), (
                "The shape of the probability for multioutput data is"
                " incorrect. Expected {}, got {}.".format(
                    (n_samples, n_classes), y_prob.shape
                )
            )
            assert_array_equal(y_prob.round().astype(int), y_pred)

    if hasattr(estimator, "decision_function") and hasattr(estimator, "predict_proba"):
        for i in range(n_classes):
            y_proba = estimator.predict_proba(X)[:, i]
            y_decision = estimator.decision_function(X)
            assert_array_equal(rankdata(y_proba), rankdata(y_decision[:, i]))