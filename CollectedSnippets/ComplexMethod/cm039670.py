def _fit_and_predict(estimator, X, y, train, test, fit_params, method):
    """Fit estimator and predict values for a given dataset split.

    Read more in the :ref:`User Guide <cross_validation>`.

    Parameters
    ----------
    estimator : estimator object implementing 'fit' and 'predict'
        The object to use to fit the data.

    X : array-like of shape (n_samples, n_features)
        The data to fit.

        .. versionchanged:: 0.20
            X is only required to be an object with finite length or shape now

    y : array-like of shape (n_samples,) or (n_samples, n_outputs) or None
        The target variable to try to predict in the case of
        supervised learning.

    train : array-like of shape (n_train_samples,)
        Indices of training samples.

    test : array-like of shape (n_test_samples,)
        Indices of test samples.

    fit_params : dict or None
        Parameters that will be passed to ``estimator.fit``.

    method : str
        Invokes the passed method name of the passed estimator.

    Returns
    -------
    predictions : sequence
        Result of calling 'estimator.method'
    """
    # Adjust length of sample weights
    fit_params = fit_params if fit_params is not None else {}
    fit_params = _check_method_params(X, params=fit_params, indices=train)

    X_train, y_train = _safe_split(estimator, X, y, train)
    X_test, _ = _safe_split(estimator, X, y, test, train)

    if y_train is None:
        estimator.fit(X_train, **fit_params)
    else:
        estimator.fit(X_train, y_train, **fit_params)
    func = getattr(estimator, method)
    predictions = func(X_test)

    encode = (
        method in ["decision_function", "predict_proba", "predict_log_proba"]
        and y is not None
    )

    if encode:
        if isinstance(predictions, list):
            predictions = [
                _enforce_prediction_order(
                    estimator.classes_[i_label],
                    predictions[i_label],
                    n_classes=len(set(y[:, i_label])),
                    method=method,
                )
                for i_label in range(len(predictions))
            ]
        else:
            # A 2D y array should be a binary label indicator matrix
            xp, _ = get_namespace(X, y)
            n_classes = (
                len(set(move_to(y, xp=np, device="cpu"))) if y.ndim == 1 else y.shape[1]
            )
            predictions = _enforce_prediction_order(
                estimator.classes_, predictions, n_classes, method
            )
    return predictions