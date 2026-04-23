def _fit_calibrator(clf, predictions, y, classes, method, xp, sample_weight=None):
    """Fit calibrator(s) and return a `_CalibratedClassifier`
    instance.

    A separate calibrator is fitted for each of the `n_classes`
    (i.e. `len(clf.classes_)`). However, if `n_classes` is 2 or if
    `method` is 'temperature', only one calibrator is fitted.

    Parameters
    ----------
    clf : estimator instance
        Fitted classifier.

    predictions : array-like, shape (n_samples, n_classes) or (n_samples, 1) \
                    when binary.
        Raw predictions returned by the un-calibrated base classifier.

    y : array-like, shape (n_samples,)
        The targets. For `method="temperature"`, `y` needs to be label encoded.

    classes : ndarray, shape (n_classes,)
        All the prediction classes.

    method : {'sigmoid', 'isotonic', 'temperature'}
        The method to use for calibration.

    xp : namespace
        Array API namespace.

    sample_weight : ndarray, shape (n_samples,), default=None
        Sample weights. If None, then samples are equally weighted.

    Returns
    -------
    pipeline : _CalibratedClassifier instance
    """
    calibrators = []

    if method in ("isotonic", "sigmoid"):
        Y = label_binarize(y, classes=classes)
        label_encoder = LabelEncoder().fit(classes)
        pos_class_indices = label_encoder.transform(clf.classes_)
        for class_idx, this_pred in zip(pos_class_indices, predictions.T):
            if method == "isotonic":
                calibrator = IsotonicRegression(out_of_bounds="clip")
            else:  # "sigmoid"
                calibrator = _SigmoidCalibration()
            calibrator.fit(this_pred, Y[:, class_idx], sample_weight)
            calibrators.append(calibrator)
    elif method == "temperature":
        if classes.shape[0] == 2 and predictions.shape[-1] == 1:
            response_method_name = _check_response_method(
                clf,
                ["decision_function", "predict_proba"],
            ).__name__
            if response_method_name == "predict_proba":
                predictions = xp.concat([1 - predictions, predictions], axis=1)
        calibrator = _TemperatureScaling()
        calibrator.fit(predictions, y, sample_weight)
        calibrators.append(calibrator)

    pipeline = _CalibratedClassifier(clf, calibrators, method=method, classes=classes)
    return pipeline