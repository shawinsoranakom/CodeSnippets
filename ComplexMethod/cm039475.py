def _validate_multiclass_probabilistic_prediction(
    y_true, y_prob, sample_weight, labels
):
    r"""Convert y_true and y_prob to shape (n_samples, n_classes)

    1. Verify that y_true, y_prob, and sample_weights have the same first dim
    2. Ensure 2 or more classes in y_true i.e. valid classification task. The
       classes are provided by the labels argument, or inferred using y_true.
       When inferring y_true is assumed binary if it has shape (n_samples, ).
    3. Validate y_true, and y_prob have the same number of classes. Convert to
       shape (n_samples, n_classes)

    Parameters
    ----------
    y_true : array-like or label indicator matrix
        Ground truth (correct) labels for n_samples samples.

    y_prob : array of floats, shape=(n_samples, n_classes) or (n_samples,)
        Predicted probabilities, as returned by a classifier's
        predict_proba method. If `y_prob.shape = (n_samples,)`
        the probabilities provided are assumed to be that of the
        positive class. The labels in `y_prob` are assumed to be
        ordered lexicographically, as done by
        :class:`preprocessing.LabelBinarizer`.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    labels : array-like, default=None
        If not provided, labels will be inferred from y_true. If `labels`
        is `None` and `y_prob` has shape `(n_samples,)` the labels are
        assumed to be binary and are inferred from `y_true`.

    Returns
    -------
    transformed_labels : array of shape (n_samples, n_classes)

    y_prob : array of shape (n_samples, n_classes)
    """
    xp, _, device_ = get_namespace_and_device(y_prob)

    if xp.max(y_prob) > 1:
        raise ValueError(f"y_prob contains values greater than 1: {xp.max(y_prob)}")
    if xp.min(y_prob) < 0:
        raise ValueError(f"y_prob contains values lower than 0: {xp.min(y_prob)}")

    check_consistent_length(y_prob, y_true, sample_weight)
    if sample_weight is not None:
        _check_sample_weight(sample_weight, y_prob, force_float_dtype=False)

    transformed_labels, lb_classes = _one_hot_encoding_multiclass_target(
        y_true=y_true, labels=labels, target_xp=xp, target_device=device_
    )

    # If y_prob is of single dimension, assume y_true to be binary
    # and then check.
    if y_prob.ndim == 1:
        y_prob = y_prob[:, xp.newaxis]
    if y_prob.shape[1] == 1:
        y_prob = xp.concat([1 - y_prob, y_prob], axis=1)

    eps = xp.finfo(y_prob.dtype).eps

    # Make sure y_prob is normalized
    y_prob_sum = xp.sum(y_prob, axis=1)

    if not xp.all(
        xpx.isclose(
            y_prob_sum,
            xp.asarray(1, dtype=y_prob_sum.dtype, device=device_),
            rtol=sqrt(eps),
        )
    ):
        warnings.warn(
            "The y_prob values do not sum to one. Make sure to pass probabilities.",
            UserWarning,
        )

    # Check if dimensions are consistent.
    if lb_classes.shape[0] != y_prob.shape[1]:
        if labels is None:
            raise ValueError(
                "y_true and y_prob contain different number of "
                "classes: {0} vs {1}. Please provide the true "
                "labels explicitly through the labels argument. "
                "Classes found in "
                "y_true: {2}".format(
                    transformed_labels.shape[1], y_prob.shape[1], lb_classes
                )
            )
        else:
            raise ValueError(
                "The number of classes in labels is different "
                "from that in y_prob. Classes found in "
                "labels: {0}".format(lb_classes)
            )

    return transformed_labels, y_prob