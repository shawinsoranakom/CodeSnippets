def confusion_matrix(
    y_true, y_pred, *, labels=None, sample_weight=None, normalize=None
):
    """Compute confusion matrix to evaluate the accuracy of a classification.

    By definition a confusion matrix :math:`C` is such that :math:`C_{i, j}`
    is equal to the number of observations known to be in group :math:`i` and
    predicted to be in group :math:`j`.

    Thus in binary classification, the count of true negatives is
    :math:`C_{0,0}`, false negatives is :math:`C_{1,0}`, true positives is
    :math:`C_{1,1}` and false positives is :math:`C_{0,1}`.

    Read more in the :ref:`User Guide <confusion_matrix>`.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth (correct) target values.

    y_pred : array-like of shape (n_samples,)
        Estimated targets as returned by a classifier.

    labels : array-like of shape (n_classes,), default=None
        List of labels to index the matrix. This may be used to reorder
        or select a subset of labels.
        If ``None`` is given, those that appear at least once
        in ``y_true`` or ``y_pred`` are used in sorted order.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

        .. versionadded:: 0.18

    normalize : {'true', 'pred', 'all'}, default=None
        Normalizes confusion matrix over the true (rows), predicted (columns)
        conditions or all the population. If None, confusion matrix will not be
        normalized.

    Returns
    -------
    C : ndarray of shape (n_classes, n_classes)
        Confusion matrix whose i-th row and j-th
        column entry indicates the number of
        samples with true label being i-th class
        and predicted label being j-th class.

    See Also
    --------
    ConfusionMatrixDisplay.from_estimator : Plot the confusion matrix
        given an estimator, the data, and the label.
    ConfusionMatrixDisplay.from_predictions : Plot the confusion matrix
        given the true and predicted labels.
    ConfusionMatrixDisplay : Confusion Matrix visualization.
    confusion_matrix_at_thresholds : For binary classification, compute true negative,
        false positive, false negative and true positive counts per threshold.

    References
    ----------
    .. [1] `Wikipedia entry for the Confusion matrix
           <https://en.wikipedia.org/wiki/Confusion_matrix>`_
           (Wikipedia and other references may use a different
           convention for axes).

    Examples
    --------
    >>> from sklearn.metrics import confusion_matrix
    >>> y_true = [2, 0, 2, 2, 0, 1]
    >>> y_pred = [0, 0, 2, 2, 0, 2]
    >>> confusion_matrix(y_true, y_pred)
    array([[2, 0, 0],
           [0, 0, 1],
           [1, 0, 2]])

    >>> y_true = ["cat", "ant", "cat", "cat", "ant", "bird"]
    >>> y_pred = ["ant", "ant", "cat", "cat", "ant", "cat"]
    >>> confusion_matrix(y_true, y_pred, labels=["ant", "bird", "cat"])
    array([[2, 0, 0],
           [0, 0, 1],
           [1, 0, 2]])

    In the binary case, we can extract true positives, etc. as follows:

    >>> tn, fp, fn, tp = confusion_matrix([0, 1, 0, 1], [1, 1, 1, 0]).ravel().tolist()
    >>> (tn, fp, fn, tp)
    (0, 2, 1, 1)
    """
    xp, _, device_ = get_namespace_and_device(y_true, y_pred, labels, sample_weight)
    y_true = check_array(
        y_true,
        dtype=None,
        ensure_2d=False,
        ensure_all_finite=False,
        ensure_min_samples=0,
    )
    y_pred = check_array(
        y_pred,
        dtype=None,
        ensure_2d=False,
        ensure_all_finite=False,
        ensure_min_samples=0,
    )
    # Convert the input arrays to NumPy (on CPU) irrespective of the original
    # namespace and device so as to be able to leverage the efficient
    # counting operations implemented by SciPy in the coo_matrix constructor.
    # The final results will be converted back to the input namespace and device
    # for the sake of consistency with other metric functions with array API support.
    y_true = move_to(y_true, xp=np, device="cpu")
    y_pred = move_to(y_pred, xp=np, device="cpu")
    if sample_weight is None:
        sample_weight = np.ones(y_true.shape[0], dtype=np.int64)
    else:
        sample_weight = move_to(sample_weight, xp=np, device="cpu")

    if len(sample_weight) > 0:
        y_type, y_true, y_pred, sample_weight = _check_targets(
            y_true, y_pred, sample_weight
        )
    else:
        # This is needed to handle the special case where y_true, y_pred and
        # sample_weight are all empty.
        # In this case we don't pass sample_weight to _check_targets that would
        # check that sample_weight is not empty and we don't reuse the returned
        # sample_weight
        y_type, y_true, y_pred, _ = _check_targets(y_true, y_pred)

    y_true, y_pred = attach_unique(y_true, y_pred)
    if y_type not in ("binary", "multiclass"):
        raise ValueError("%s is not supported" % y_type)

    if labels is None:
        labels = unique_labels(y_true, y_pred)
    else:
        labels = move_to(labels, xp=np, device="cpu")
        n_labels = labels.size
        if n_labels == 0:
            raise ValueError("'labels' should contain at least one label.")
        elif y_true.size == 0:
            return np.zeros((n_labels, n_labels), dtype=int)
        elif len(np.intersect1d(y_true, labels)) == 0:
            raise ValueError("At least one label specified must be in y_true")

    n_labels = labels.size
    # If labels are not consecutive integers starting from zero, then
    # y_true and y_pred must be converted into index form
    need_index_conversion = not (
        labels.dtype.kind in {"i", "u", "b"}
        and np.all(labels == np.arange(n_labels))
        and y_true.min() >= 0
        and y_pred.min() >= 0
    )
    if need_index_conversion:
        label_to_ind = {label: index for index, label in enumerate(labels)}
        y_pred = np.array([label_to_ind.get(label, n_labels + 1) for label in y_pred])
        y_true = np.array([label_to_ind.get(label, n_labels + 1) for label in y_true])

    # intersect y_pred, y_true with labels, eliminate items not in labels
    ind = np.logical_and(y_pred < n_labels, y_true < n_labels)
    if not np.all(ind):
        y_pred = y_pred[ind]
        y_true = y_true[ind]
        # also eliminate weights of eliminated items
        sample_weight = sample_weight[ind]

    # Choose the accumulator dtype to always have high precision
    if sample_weight.dtype.kind in {"i", "u", "b"}:
        dtype = np.int64
    else:
        dtype = np.float32 if str(device_).startswith("mps") else np.float64

    cm = coo_array(
        (sample_weight, (y_true, y_pred)),
        shape=(n_labels, n_labels),
        dtype=dtype,
    ).toarray()

    with np.errstate(all="ignore"):
        if normalize == "true":
            cm = cm / cm.sum(axis=1, keepdims=True)
        elif normalize == "pred":
            cm = cm / cm.sum(axis=0, keepdims=True)
        elif normalize == "all":
            cm = cm / cm.sum()
        cm = xpx.nan_to_num(cm)

    if cm.shape == (1, 1):
        warnings.warn(
            (
                "A single label was found in 'y_true' and 'y_pred'. For the confusion "
                "matrix to have the correct shape, use the 'labels' parameter to pass "
                "all known labels."
            ),
            UserWarning,
        )

    return xp.asarray(cm, device=device_)