def _average_binary_score(binary_metric, y_true, y_score, average, sample_weight=None):
    """Average a binary metric for multilabel classification.

    Parameters
    ----------
    binary_metric : callable, returns shape [n_classes]
        The binary metric function to use.

    y_true : array, shape = [n_samples] or [n_samples, n_classes]
        True binary labels in binary label indicators.

    y_score : array, shape = [n_samples] or [n_samples, n_classes]
        Target scores, can either be probability estimates of the positive
        class or non-thresholded decision values (as returned by
        :term:`decision_function` on some classifiers).

    average : {None, 'micro', 'macro', 'samples', 'weighted'}, default='macro'
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

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    Returns
    -------
    score : float or array of shape [n_classes]
        If not ``None``, average the score, else return the score for each
        classes.

    """
    xp, _, _device = get_namespace_and_device(y_score, sample_weight)
    average_options = (None, "micro", "macro", "weighted", "samples")
    if average not in average_options:
        raise ValueError("average has to be one of {0}".format(average_options))

    y_type = type_of_target(y_true)
    if y_type not in ("binary", "multilabel-indicator"):
        raise ValueError("{0} format is not supported".format(y_type))

    if y_type == "binary":
        return binary_metric(y_true, y_score, sample_weight=sample_weight)

    check_consistent_length(y_true, y_score, sample_weight)
    y_true = check_array(y_true)
    y_score = check_array(y_score)

    not_average_axis = 1
    score_weight = sample_weight
    average_weight = None

    if average == "micro":
        if score_weight is not None:
            score_weight = xp.repeat(score_weight, y_true.shape[1])
        y_true = _ravel(y_true)
        y_score = _ravel(y_score)

    elif average == "weighted":
        if score_weight is not None:
            #  Mixed integer and float type promotion not defined in array standard
            y_true = xp.asarray(y_true, dtype=score_weight.dtype)
            average_weight = xp.sum(
                xp.multiply(y_true, xp.reshape(score_weight, (-1, 1))), axis=0
            )
        else:
            average_weight = xp.sum(y_true, axis=0)
        if xpx.isclose(
            xp.sum(average_weight),
            xp.asarray(0, dtype=average_weight.dtype, device=_device),
        ):
            return 0

    elif average == "samples":
        # swap average_weight <-> score_weight
        average_weight = score_weight
        score_weight = None
        not_average_axis = 0

    if y_true.ndim == 1:
        y_true = xp.reshape(y_true, (-1, 1))

    if y_score.ndim == 1:
        y_score = xp.reshape(y_score, (-1, 1))

    n_classes = y_score.shape[not_average_axis]
    score = xp.zeros((n_classes,), device=_device)
    for c in range(n_classes):
        y_true_c = _ravel(
            xp.take(y_true, xp.asarray([c], device=_device), axis=not_average_axis)
        )
        y_score_c = _ravel(
            xp.take(y_score, xp.asarray([c], device=_device), axis=not_average_axis)
        )
        score[c] = binary_metric(y_true_c, y_score_c, sample_weight=score_weight)

    # Average the results
    if average is not None:
        if average_weight is not None:
            # Scores with 0 weights are forced to be 0, preventing the average
            # score from being affected by 0-weighted NaN elements.
            score[average_weight == 0] = 0
        return float(_average(score, weights=average_weight, xp=xp))
    else:
        return score