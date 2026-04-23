def _get_response_values(
    estimator,
    X,
    response_method,
    pos_label=None,
    return_response_method_used=False,
):
    """Compute the response values of a classifier, an outlier detector, a regressor
    or a clusterer.

    The response values are predictions such that it follows the following shape:

    - for binary classification, it is a 1d array of shape `(n_samples,)`;
    - for multiclass classification
        - with response_method="predict", it is a 1d array of shape `(n_samples,)`;
        - otherwise, it is a 2d array of shape `(n_samples, n_classes)`;
    - for multilabel classification, it is a 2d array of shape `(n_samples, n_outputs)`;
    - for outlier detection, a regressor or a clusterer, it is a 1d array of shape
      `(n_samples,)`.

    If `estimator` is a binary classifier, also return the label for the
    effective positive class.

    This utility is used primarily in the displays and the scikit-learn scorers.

    .. versionadded:: 1.3

    Parameters
    ----------
    estimator : estimator instance
        Fitted classifier, outlier detector, regressor, clusterer or a
        fitted :class:`~sklearn.pipeline.Pipeline` in which the last estimator is a
        classifier, an outlier detector, a regressor or a clusterer.

    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Input values.

    response_method : {"predict_proba", "predict_log_proba", "decision_function", \
            "predict"} or list of such str
        Specifies the response method to use get prediction from an estimator
        (i.e. :term:`predict_proba`, :term:`predict_log_proba`,
        :term:`decision_function` or :term:`predict`). Possible choices are:

        - if `str`, it corresponds to the name to the method to return;
        - if a list of `str`, it provides the method names in order of
          preference. The method returned corresponds to the first method in
          the list and which is implemented by `estimator`.

    pos_label : int, float, bool or str, default=None
        The class considered as the positive class when computing
        the response values. If `None` and target is 'binary',
        `estimators.classes_[1]` is considered as the positive class.

    return_response_method_used : bool, default=False
        Whether to return the response method used to compute the response
        values.

        .. versionadded:: 1.4

    Returns
    -------
    y_pred : ndarray of shape (n_samples,), (n_samples, n_classes) or \
            (n_samples, n_outputs)
        Target scores calculated from the provided `response_method`
        and `pos_label`.

    pos_label : int, float, bool, str or None
        The class considered as the positive class when computing
        binary response values. Returns `None` if `estimator` is a regressor, an outlier
        detector or a clusterer.

    response_method_used : str
        The response method used to compute the response values. Only returned
        if `return_response_method_used` is `True`.

        .. versionadded:: 1.4

    Raises
    ------
    ValueError
        If `pos_label` is not a valid label.
        If the shape of `y_pred` is not consistent for binary classifier.
    """
    prediction_method = _check_response_method(estimator, response_method)

    if is_classifier(estimator):
        classes = estimator.classes_
        target_type = type_of_target(classes)

        if target_type == "binary":
            if pos_label is not None and pos_label not in classes.tolist():
                raise ValueError(
                    f"pos_label={pos_label} is not a valid label: It should be "
                    f"one of {classes}"
                )
            elif pos_label is None:
                pos_label = classes[-1]

        y_pred = prediction_method(X)

        if prediction_method.__name__ in ("predict_proba", "predict_log_proba"):
            y_pred = _process_predict_proba(
                y_pred=y_pred,
                target_type=target_type,
                classes=classes,
                pos_label=pos_label,
            )
        elif prediction_method.__name__ == "decision_function":
            y_pred = _process_decision_function(
                y_pred=y_pred,
                target_type=target_type,
                classes=classes,
                pos_label=pos_label,
            )
    else:
        y_pred, pos_label = prediction_method(X), None

    if return_response_method_used:
        return y_pred, pos_label, prediction_method.__name__
    return y_pred, pos_label