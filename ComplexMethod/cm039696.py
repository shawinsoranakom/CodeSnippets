def check_cross_val_predict_multilabel(est, X, y, method):
    """Check the output of cross_val_predict for 2D targets using
    Estimators which provide a predictions as a list with one
    element per class.
    """
    cv = KFold(n_splits=3, shuffle=False)

    # Create empty arrays of the correct size to hold outputs
    float_min = np.finfo(np.float64).min
    default_values = {
        "decision_function": float_min,
        "predict_log_proba": float_min,
        "predict_proba": 0,
    }
    n_targets = y.shape[1]
    expected_preds = []
    for i_col in range(n_targets):
        n_classes_in_label = len(set(y[:, i_col]))
        if n_classes_in_label == 2 and method == "decision_function":
            exp_shape = (len(X),)
        else:
            exp_shape = (len(X), n_classes_in_label)
        expected_preds.append(
            np.full(exp_shape, default_values[method], dtype=np.float64)
        )

    # Generate expected outputs
    y_enc_cols = [
        np.unique(y[:, i], return_inverse=True)[1][:, np.newaxis]
        for i in range(y.shape[1])
    ]
    y_enc = np.concatenate(y_enc_cols, axis=1)
    for train, test in cv.split(X, y_enc):
        est = clone(est).fit(X[train], y_enc[train])
        fold_preds = getattr(est, method)(X[test])
        for i_col in range(n_targets):
            fold_cols = np.unique(y_enc[train][:, i_col])
            if expected_preds[i_col].ndim == 1:
                # Decision function with <=2 classes
                expected_preds[i_col][test] = fold_preds[i_col]
            else:
                idx = np.ix_(test, fold_cols)
                expected_preds[i_col][idx] = fold_preds[i_col]

    # Check actual outputs for several representations of y
    for tg in [y, y + 1, y - 2, y.astype("str")]:
        cv_predict_output = cross_val_predict(est, X, tg, method=method, cv=cv)
        assert len(cv_predict_output) == len(expected_preds)
        for i in range(len(cv_predict_output)):
            assert_allclose(cv_predict_output[i], expected_preds[i])