def multilabel_confusion_matrix(
    y_true, y_pred, *, sample_weight=None, labels=None, samplewise=False
):
    """Compute a confusion matrix for each class or sample.

    .. versionadded:: 0.21

    Compute class-wise (default) or sample-wise (samplewise=True) multilabel
    confusion matrix to evaluate the accuracy of a classification, and output
    confusion matrices for each class or sample.

    In multilabel confusion matrix :math:`MCM`, the count of true negatives
    is :math:`MCM_{:,0,0}`, false negatives is :math:`MCM_{:,1,0}`,
    true positives is :math:`MCM_{:,1,1}` and false positives is
    :math:`MCM_{:,0,1}`.

    Multiclass data will be treated as if binarized under a one-vs-rest
    transformation. Returned confusion matrices will be in the order of
    sorted unique labels in the union of (y_true, y_pred).

    Read more in the :ref:`User Guide <multilabel_confusion_matrix>`.

    Parameters
    ----------
    y_true : {array-like, sparse matrix} of shape (n_samples, n_outputs) or \
            (n_samples,)
        Ground truth (correct) target values. Sparse matrix is only supported when
        labels are of :term:`multilabel` type.

    y_pred : {array-like, sparse matrix} of shape (n_samples, n_outputs) or \
            (n_samples,)
        Estimated targets as returned by a classifier. Sparse matrix is only
        supported when labels are of :term:`multilabel` type.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    labels : array-like of shape (n_classes,), default=None
        A list of classes or column indices to select some (or to force
        inclusion of classes absent from the data).

    samplewise : bool, default=False
        In the multilabel case, this calculates a confusion matrix per sample.

    Returns
    -------
    multi_confusion : ndarray of shape (n_outputs, 2, 2)
        A 2x2 confusion matrix corresponding to each output in the input.
        When calculating class-wise multi_confusion (default), then
        n_outputs = n_labels; when calculating sample-wise multi_confusion
        (samplewise=True), n_outputs = n_samples. If ``labels`` is defined,
        the results will be returned in the order specified in ``labels``,
        otherwise the results will be returned in sorted order by default.

    See Also
    --------
    confusion_matrix : Compute confusion matrix to evaluate the accuracy of a
        classifier.

    Notes
    -----
    The `multilabel_confusion_matrix` calculates class-wise or sample-wise
    multilabel confusion matrices, and in multiclass tasks, labels are
    binarized under a one-vs-rest way; while
    :func:`~sklearn.metrics.confusion_matrix` calculates one confusion matrix
    for confusion between every two classes.

    Examples
    --------
    Multilabel-indicator case:

    >>> import numpy as np
    >>> from sklearn.metrics import multilabel_confusion_matrix
    >>> y_true = np.array([[1, 0, 1],
    ...                    [0, 1, 0]])
    >>> y_pred = np.array([[1, 0, 0],
    ...                    [0, 1, 1]])
    >>> multilabel_confusion_matrix(y_true, y_pred)
    array([[[1, 0],
            [0, 1]],
    <BLANKLINE>
           [[1, 0],
            [0, 1]],
    <BLANKLINE>
           [[0, 1],
            [1, 0]]])

    Multiclass case:

    >>> y_true = ["cat", "ant", "cat", "cat", "ant", "bird"]
    >>> y_pred = ["ant", "ant", "cat", "cat", "ant", "cat"]
    >>> multilabel_confusion_matrix(y_true, y_pred,
    ...                             labels=["ant", "bird", "cat"])
    array([[[3, 1],
            [0, 2]],
    <BLANKLINE>
           [[5, 0],
            [1, 0]],
    <BLANKLINE>
           [[2, 1],
            [1, 2]]])
    """
    y_true, y_pred = attach_unique(y_true, y_pred)
    xp, _, device_ = get_namespace_and_device(y_pred)
    y_true, sample_weight = move_to(y_true, sample_weight, xp=xp, device=device_)
    y_type, y_true, y_pred, sample_weight = _check_targets(
        y_true, y_pred, sample_weight
    )

    if y_type not in ("binary", "multiclass", "multilabel-indicator"):
        raise ValueError("%s is not supported" % y_type)

    present_labels = unique_labels(y_true, y_pred)
    if labels is None:
        labels = present_labels
        n_labels = None
    else:
        labels = xp.asarray(labels, device=device_)
        n_labels = labels.shape[0]
        labels = xp.concat(
            [labels, xpx.setdiff1d(present_labels, labels, assume_unique=True, xp=xp)],
            axis=-1,
        )

    if y_true.ndim == 1:
        if samplewise:
            raise ValueError(
                "Samplewise metrics are not available outside of "
                "multilabel classification."
            )

        le = LabelEncoder()
        le.fit(labels)
        y_true = le.transform(y_true)
        y_pred = le.transform(y_pred)
        sorted_labels = le.classes_

        # labels are now from 0 to len(labels) - 1 -> use bincount
        tp = y_true == y_pred
        tp_bins = y_true[tp]
        if sample_weight is not None:
            tp_bins_weights = sample_weight[tp]
        else:
            tp_bins_weights = None

        if tp_bins.shape[0]:
            tp_sum = _bincount(
                tp_bins, weights=tp_bins_weights, minlength=labels.shape[0], xp=xp
            )
        else:
            # Pathological case
            true_sum = pred_sum = tp_sum = xp.zeros(labels.shape[0])
        if y_pred.shape[0]:
            pred_sum = _bincount(
                y_pred, weights=sample_weight, minlength=labels.shape[0], xp=xp
            )
        if y_true.shape[0]:
            true_sum = _bincount(
                y_true, weights=sample_weight, minlength=labels.shape[0], xp=xp
            )

        # Retain only selected labels
        indices = xp.searchsorted(sorted_labels, labels[:n_labels])
        tp_sum = xp.take(tp_sum, indices, axis=0)
        true_sum = xp.take(true_sum, indices, axis=0)
        pred_sum = xp.take(pred_sum, indices, axis=0)

    else:
        sum_axis = 1 if samplewise else 0

        # All labels are index integers for multilabel.
        # Select labels:
        if labels.shape != present_labels.shape or xp.any(
            xp.not_equal(labels, present_labels)
        ):
            if xp.max(labels) > xp.max(present_labels):
                raise ValueError(
                    "All labels must be in [0, n labels) for "
                    "multilabel targets. "
                    "Got %d > %d" % (xp.max(labels), xp.max(present_labels))
                )
            if xp.min(labels) < 0:
                raise ValueError(
                    "All labels must be in [0, n labels) for "
                    "multilabel targets. "
                    "Got %d < 0" % xp.min(labels)
                )

        if n_labels is not None:
            y_true = y_true[:, labels[:n_labels]]
            y_pred = y_pred[:, labels[:n_labels]]

        if issparse(y_true) or issparse(y_pred):
            true_and_pred = y_true.multiply(y_pred)
        else:
            true_and_pred = xp.multiply(y_true, y_pred)

        # calculate weighted counts
        tp_sum = _count_nonzero(
            true_and_pred,
            axis=sum_axis,
            sample_weight=sample_weight,
            xp=xp,
            device=device_,
        )
        pred_sum = _count_nonzero(
            y_pred,
            axis=sum_axis,
            sample_weight=sample_weight,
            xp=xp,
            device=device_,
        )
        true_sum = _count_nonzero(
            y_true,
            axis=sum_axis,
            sample_weight=sample_weight,
            xp=xp,
            device=device_,
        )

    fp = pred_sum - tp_sum
    fn = true_sum - tp_sum
    tp = tp_sum

    if sample_weight is not None and samplewise:
        tp = xp.asarray(tp)
        fp = xp.asarray(fp)
        fn = xp.asarray(fn)
        tn = sample_weight * y_true.shape[1] - tp - fp - fn
    elif sample_weight is not None:
        tn = xp.sum(sample_weight) - tp - fp - fn
    elif samplewise:
        tn = y_true.shape[1] - tp - fp - fn
    else:
        tn = y_true.shape[0] - tp - fp - fn

    return xp.reshape(xp.stack([tn, fp, fn, tp]).T, (-1, 2, 2))