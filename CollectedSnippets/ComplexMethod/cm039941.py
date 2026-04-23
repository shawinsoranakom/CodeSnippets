def test_get_response_values_multilabel_indicator(response_method):
    X, Y = make_multilabel_classification(random_state=0)
    estimator = ClassifierChain(LogisticRegression()).fit(X, Y)

    y_pred, pos_label = _get_response_values(
        estimator, X, response_method=response_method
    )
    assert pos_label is None
    assert y_pred.shape == Y.shape

    if response_method == "predict_proba":
        assert np.logical_and(y_pred >= 0, y_pred <= 1).all()
    elif response_method == "decision_function":
        # values returned by `decision_function` are not bounded in [0, 1]
        assert (y_pred < 0).sum() > 0
        assert (y_pred > 1).sum() > 0
    else:  # response_method == "predict"
        assert np.logical_or(y_pred == 0, y_pred == 1).all()