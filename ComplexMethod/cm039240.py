def _partial_dependence_brute(
    est, grid, features, X, response_method, sample_weight=None
):
    """Calculate partial dependence via the brute force method.

    The brute method explicitly averages the predictions of an estimator over a
    grid of feature values.

    For each `grid` value, all the samples from `X` have their variables of
    interest replaced by that specific `grid` value. The predictions are then made
    and averaged across the samples.

    This method is slower than the `'recursion'`
    (:func:`~sklearn.inspection._partial_dependence._partial_dependence_recursion`)
    version for estimators with this second option. However, with the `'brute'`
    force method, the average will be done with the given `X` and not the `X`
    used during training, as it is done in the `'recursion'` version. Therefore
    the average can always accept `sample_weight` (even when the estimator was
    fitted without).

    Parameters
    ----------
    est : BaseEstimator
        A fitted estimator object implementing :term:`predict`,
        :term:`predict_proba`, or :term:`decision_function`.
        Multioutput-multiclass classifiers are not supported.

    grid : array-like of shape (n_points, n_target_features)
        The grid of feature values for which the partial dependence is calculated.
        Note that `n_points` is the number of points in the grid and `n_target_features`
        is the number of features you are doing partial dependence at.

    features : array-like of {int, str}
        The feature (e.g. `[0]`) or pair of interacting features
        (e.g. `[(0, 1)]`) for which the partial dependency should be computed.

    X : array-like of shape (n_samples, n_features)
        `X` is used to generate values for the complement features. That is, for
        each value in `grid`, the method will average the prediction of each
        sample from `X` having that grid value for `features`.

    response_method : {'auto', 'predict_proba', 'decision_function'}, \
            default='auto'
        Specifies whether to use :term:`predict_proba` or
        :term:`decision_function` as the target response. For regressors
        this parameter is ignored and the response is always the output of
        :term:`predict`. By default, :term:`predict_proba` is tried first
        and we revert to :term:`decision_function` if it doesn't exist.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights are used to calculate weighted means when averaging the
        model output. If `None`, then samples are equally weighted. Note that
        `sample_weight` does not change the individual predictions.

    Returns
    -------
    averaged_predictions : array-like of shape (n_targets, n_points)
        The averaged predictions for the given `grid` of features values.
        Note that `n_targets` is the number of targets (e.g. 1 for binary
        classification, `n_tasks` for multi-output regression, and `n_classes` for
        multiclass classification) and `n_points` is the number of points in the `grid`.

    predictions : array-like
        The predictions for the given `grid` of features values over the samples
        from `X`. For non-multioutput regression and binary classification the
        shape is `(n_instances, n_points)` and for multi-output regression and
        multiclass classification the shape is `(n_targets, n_instances, n_points)`,
        where `n_targets` is the number of targets (`n_tasks` for multi-output
        regression, and `n_classes` for multiclass classification), `n_instances`
        is the number of instances in `X`, and `n_points` is the number of points
        in the `grid`.
    """
    predictions = []
    averaged_predictions = []

    if response_method == "auto":
        response_method = (
            "predict" if is_regressor(est) else ["predict_proba", "decision_function"]
        )

    X_eval = X.copy()
    for new_values in grid:
        for i, variable in enumerate(features):
            _safe_assign(X_eval, new_values[i], column_indexer=variable)

        # Note: predictions is of shape
        # (n_points,) for non-multioutput regressors
        # (n_points, n_tasks) for multioutput regressors
        # (n_points, 1) for the regressors in cross_decomposition (I think)
        # (n_points, 1) for binary classification (positive class already selected)
        # (n_points, n_classes) for multiclass classification
        pred, _ = _get_response_values(est, X_eval, response_method=response_method)

        predictions.append(pred)
        # average over samples
        averaged_predictions.append(np.average(pred, axis=0, weights=sample_weight))

    n_samples = X.shape[0]

    # reshape to (n_targets, n_instances, n_points) where n_targets is:
    # - 1 for non-multioutput regression and binary classification (shape is
    #   already correct in those cases)
    # - n_tasks for multi-output regression
    # - n_classes for multiclass classification.
    predictions = np.array(predictions).T
    if is_regressor(est) and predictions.ndim == 2:
        # non-multioutput regression, shape is (n_instances, n_points,)
        predictions = predictions.reshape(n_samples, -1)
    elif is_classifier(est) and predictions.shape[0] == 2:
        # Binary classification, shape is (2, n_instances, n_points).
        # we output the effect of **positive** class
        predictions = predictions[1]
        predictions = predictions.reshape(n_samples, -1)

    # reshape averaged_predictions to (n_targets, n_points) where n_targets is:
    # - 1 for non-multioutput regression and binary classification (shape is
    #   already correct in those cases)
    # - n_tasks for multi-output regression
    # - n_classes for multiclass classification.
    averaged_predictions = np.array(averaged_predictions).T
    if averaged_predictions.ndim == 1:
        # reshape to (1, n_points) for consistency with
        # _partial_dependence_recursion
        averaged_predictions = averaged_predictions.reshape(1, -1)

    return averaged_predictions, predictions