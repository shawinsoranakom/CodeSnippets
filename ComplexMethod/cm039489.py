def average_precision_score(
    y_true, y_score, *, average="macro", pos_label=1, sample_weight=None
):
    """Compute average precision (AP) from prediction scores.

    AP summarizes a precision-recall curve as the weighted mean of precisions
    achieved at each threshold, with the increase in recall from the previous
    threshold used as the weight:

    .. math::
        \\text{AP} = \\sum_n (R_n - R_{n-1}) P_n

    where :math:`P_n` and :math:`R_n` are the precision and recall at the nth
    threshold [1]_. This implementation is not interpolated and is different
    from computing the area under the precision-recall curve with the
    trapezoidal rule, which uses linear interpolation and can be too
    optimistic.

    Read more in the :ref:`User Guide <precision_recall_f_measure_metrics>`.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_classes)
        True binary labels, :term:`multi-label` indicators (as a
        :term:`multilabel indicator matrix`) or :term:`multi-class` labels.

    y_score : array-like of shape (n_samples,) or (n_samples, n_classes)
        Target scores, can either be probability estimates of the positive
        class or non-thresholded decision values (as returned by
        :term:`decision_function` on some classifiers).
        For :term:`decision_function` scores, values greater than or equal to
        zero should indicate the positive class.

    average : {'micro', 'samples', 'weighted', 'macro'} or None, \
            default='macro'
        If ``None``, the scores for each class are returned. Otherwise,
        this determines the type of averaging performed on the data:

        ``'micro'``:
            Calculate metrics globally by considering each element of the label
            indicator matrix as a label.
        ``'macro'``:
            Calculate metrics for each label, and find their unweighted
            mean.  This does not take label imbalance into account.
        ``'weighted'``:
            Calculate metrics for each label, and find their average, weighted
            by support (the number of true instances for each label).
        ``'samples'``:
            Calculate metrics for each instance, and find their average.

        Will be ignored when ``y_true`` is binary.

    pos_label : int, float, bool or str, default=1
        The label of the positive class. Only applied to binary ``y_true``.
        For multilabel-indicator ``y_true``, ``pos_label`` is fixed to 1.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    Returns
    -------
    average_precision : float
        Average precision score.

    See Also
    --------
    roc_auc_score : Compute the area under the ROC curve.
    precision_recall_curve : Compute precision-recall pairs for different
        probability thresholds.
    PrecisionRecallDisplay.from_estimator : Plot the precision recall curve
        using an estimator and data.
    PrecisionRecallDisplay.from_predictions : Plot the precision recall curve
        using true and predicted labels.

    Notes
    -----
    .. versionchanged:: 0.19
      Instead of linearly interpolating between operating points, precisions
      are weighted by the change in recall since the last operating point.

    References
    ----------
    .. [1] `Wikipedia entry for the Average precision
           <https://en.wikipedia.org/w/index.php?title=Information_retrieval&
           oldid=793358396#Average_precision>`_

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.metrics import average_precision_score
    >>> y_true = np.array([0, 0, 1, 1])
    >>> y_scores = np.array([0.1, 0.4, 0.35, 0.8])
    >>> average_precision_score(y_true, y_scores)
    0.83
    >>> y_true = np.array([0, 0, 1, 1, 2, 2])
    >>> y_scores = np.array([
    ...     [0.7, 0.2, 0.1],
    ...     [0.4, 0.3, 0.3],
    ...     [0.1, 0.8, 0.1],
    ...     [0.2, 0.3, 0.5],
    ...     [0.4, 0.4, 0.2],
    ...     [0.1, 0.2, 0.7],
    ... ])
    >>> average_precision_score(y_true, y_scores)
    0.77
    """
    xp, _, device = get_namespace_and_device(y_score)
    # To allow mixed string `y_true`/numeric `y_score` input, cannot move `y_true`
    # until it has been converted to an integer (e.g., via `label_binarize`)
    # Ensures `test_array_api_classification_mixed_string_numeric_input` passes.
    sample_weight = move_to(sample_weight, xp=xp, device=device)

    if sample_weight is not None:
        sample_weight = column_or_1d(sample_weight)

    def _binary_uninterpolated_average_precision(
        y_true,
        y_score,
        pos_label=1,
        sample_weight=None,
        xp=xp,
    ):
        precision, recall, _ = precision_recall_curve(
            y_true,
            y_score,
            pos_label=pos_label,
            sample_weight=sample_weight,
        )
        # Return the step function integral
        # The following works because the last entry of precision is
        # guaranteed to be 1, as returned by precision_recall_curve.
        # Due to numerical error, we can get `-0.0` and we therefore clip it.
        return float(max(0.0, -xp.sum(xp.diff(recall) * precision[:-1])))

    y_type = type_of_target(y_true, input_name="y_true")
    xp_y_true, _ = get_namespace(y_true)
    present_labels = xp_y_true.unique_values(y_true)

    if y_type == "binary":
        if present_labels.shape[0] == 2 and pos_label not in present_labels:
            raise ValueError(
                f"pos_label={pos_label} is not a valid label. It should be "
                f"one of {present_labels}"
            )

    elif y_type == "multilabel-indicator" and pos_label != 1:
        raise ValueError(
            "Parameter pos_label is fixed to 1 for multilabel-indicator y_true. "
            "Do not set pos_label or set pos_label to 1."
        )

    elif y_type == "multiclass":
        if pos_label != 1:
            raise ValueError(
                "Parameter pos_label is fixed to 1 for multiclass y_true. "
                "Do not set pos_label or set pos_label to 1."
            )
        y_true = label_binarize(y_true, classes=present_labels)
        y_true = move_to(y_true, xp=xp, device=device)
        if not y_score.shape == y_true.shape:
            raise ValueError(
                "`y_score` needs to be of shape `(n_samples, n_classes)`, since "
                "`y_true` contains multiple classes. Got "
                f"`y_score.shape={y_score.shape}`."
            )

    average_precision = partial(
        _binary_uninterpolated_average_precision, pos_label=pos_label, xp=xp
    )
    return _average_binary_score(
        average_precision, y_true, y_score, average, sample_weight=sample_weight
    )