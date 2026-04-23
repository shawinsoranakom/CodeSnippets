def class_likelihood_ratios(
    y_true,
    y_pred,
    *,
    labels=None,
    sample_weight=None,
    replace_undefined_by=np.nan,
):
    """Compute binary classification positive and negative likelihood ratios.

    The positive likelihood ratio is `LR+ = sensitivity / (1 - specificity)`
    where the sensitivity or recall is the ratio `tp / (tp + fn)` and the
    specificity is `tn / (tn + fp)`. The negative likelihood ratio is `LR- = (1
    - sensitivity) / specificity`. Here `tp` is the number of true positives,
    `fp` the number of false positives, `tn` is the number of true negatives and
    `fn` the number of false negatives. Both class likelihood ratios can be used
    to obtain post-test probabilities given a pre-test probability.

    `LR+` ranges from 1.0 to infinity. A `LR+` of 1.0 indicates that the probability
    of predicting the positive class is the same for samples belonging to either
    class; therefore, the test is useless. The greater `LR+` is, the more a
    positive prediction is likely to be a true positive when compared with the
    pre-test probability. A value of `LR+` lower than 1.0 is invalid as it would
    indicate that the odds of a sample being a true positive decrease with
    respect to the pre-test odds.

    `LR-` ranges from 0.0 to 1.0. The closer it is to 0.0, the lower the probability
    of a given sample to be a false negative. A `LR-` of 1.0 means the test is
    useless because the odds of having the condition did not change after the
    test. A value of `LR-` greater than 1.0 invalidates the classifier as it
    indicates an increase in the odds of a sample belonging to the positive
    class after being classified as negative. This is the case when the
    classifier systematically predicts the opposite of the true label.

    A typical application in medicine is to identify the positive/negative class
    to the presence/absence of a disease, respectively; the classifier being a
    diagnostic test; the pre-test probability of an individual having the
    disease can be the prevalence of such disease (proportion of a particular
    population found to be affected by a medical condition); and the post-test
    probabilities would be the probability that the condition is truly present
    given a positive test result.

    Read more in the :ref:`User Guide <class_likelihood_ratios>`.

    Parameters
    ----------
    y_true : 1d array-like, or label indicator array / sparse matrix
        Ground truth (correct) target values. Sparse matrix is only supported when
        targets are of :term:`multilabel` type.

    y_pred : 1d array-like, or label indicator array / sparse matrix
        Estimated targets as returned by a classifier. Sparse matrix is only
        supported when targets are of :term:`multilabel` type.

    labels : array-like, default=None
        List of labels to index the matrix. This may be used to select the
        positive and negative classes with the ordering `labels=[negative_class,
        positive_class]`. If `None` is given, those that appear at least once in
        `y_true` or `y_pred` are used in sorted order.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    replace_undefined_by : np.nan, 1.0, or dict, default=np.nan
        Sets the return values for LR+ and LR- when there is a division by zero. Can
        take the following values:

        - `np.nan` to return `np.nan` for both `LR+` and `LR-`
        - `1.0` to return the worst possible scores: `{"LR+": 1.0, "LR-": 1.0}`
        - a dict in the format `{"LR+": value_1, "LR-": value_2}` where the values can
          be non-negative floats, `np.inf` or `np.nan` in the range of the
          likelihood ratios. For example, `{"LR+": 1.0, "LR-": 1.0}` can be used for
          returning the worst scores, indicating a useless model, and `{"LR+": np.inf,
          "LR-": 0.0}` can be used for returning the best scores, indicating a useful
          model.

        If a division by zero occurs, only the affected metric is replaced with the set
        value; the other metric is calculated as usual.

        .. versionadded:: 1.7

    Returns
    -------
    (positive_likelihood_ratio, negative_likelihood_ratio) : tuple of float
        A tuple of two floats, the first containing the positive likelihood ratio (LR+)
        and the second the negative likelihood ratio (LR-).

    Warns
    -----
    Raises :class:`~sklearn.exceptions.UndefinedMetricWarning` when `y_true` and
    `y_pred` lead to the following conditions:

        - The number of false positives is 0: positive likelihood ratio is undefined.
        - The number of true negatives is 0: negative likelihood ratio is undefined.
        - The sum of true positives and false negatives is 0 (no samples of the positive
          class are present in `y_true`): both likelihood ratios are undefined.

        For the first two cases, an undefined metric can be defined by setting the
        `replace_undefined_by` param.

    References
    ----------
    .. [1] `Wikipedia entry for the Likelihood ratios in diagnostic testing
           <https://en.wikipedia.org/wiki/Likelihood_ratios_in_diagnostic_testing>`_.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.metrics import class_likelihood_ratios
    >>> class_likelihood_ratios([0, 1, 0, 1, 0], [1, 1, 0, 0, 0])
    (1.5, 0.75)
    >>> y_true = np.array(["non-cat", "cat", "non-cat", "cat", "non-cat"])
    >>> y_pred = np.array(["cat", "cat", "non-cat", "non-cat", "non-cat"])
    >>> class_likelihood_ratios(y_true, y_pred)
    (1.33, 0.66)
    >>> y_true = np.array(["non-zebra", "zebra", "non-zebra", "zebra", "non-zebra"])
    >>> y_pred = np.array(["zebra", "zebra", "non-zebra", "non-zebra", "non-zebra"])
    >>> class_likelihood_ratios(y_true, y_pred)
    (1.5, 0.75)

    To avoid ambiguities, use the notation `labels=[negative_class,
    positive_class]`

    >>> y_true = np.array(["non-cat", "cat", "non-cat", "cat", "non-cat"])
    >>> y_pred = np.array(["cat", "cat", "non-cat", "non-cat", "non-cat"])
    >>> class_likelihood_ratios(y_true, y_pred, labels=["non-cat", "cat"])
    (1.5, 0.75)
    """
    y_true, y_pred = attach_unique(y_true, y_pred)
    y_type, y_true, y_pred, sample_weight = _check_targets(
        y_true, y_pred, sample_weight
    )
    if y_type != "binary":
        raise ValueError(
            "class_likelihood_ratios only supports binary classification "
            f"problems, got targets of type: {y_type}"
        )

    if replace_undefined_by == 1.0:
        replace_undefined_by = {"LR+": 1.0, "LR-": 1.0}

    if isinstance(replace_undefined_by, dict):
        msg = (
            "The dictionary passed as `replace_undefined_by` needs to be in the form "
            "`{'LR+': `value_1`, 'LR-': `value_2`}` where the value for `LR+` ranges "
            "from `1.0` to `np.inf` or is `np.nan` and the value for `LR-` ranges from "
            f"`0.0` to `1.0` or is `np.nan`; got `{replace_undefined_by}`."
        )
        if ("LR+" in replace_undefined_by) and ("LR-" in replace_undefined_by):
            try:
                desired_lr_pos = replace_undefined_by.get("LR+", None)
                check_scalar(
                    desired_lr_pos,
                    "positive_likelihood_ratio",
                    target_type=(Real),
                    min_val=1.0,
                    include_boundaries="left",
                )
                desired_lr_neg = replace_undefined_by.get("LR-", None)
                check_scalar(
                    desired_lr_neg,
                    "negative_likelihood_ratio",
                    target_type=(Real),
                    min_val=0.0,
                    max_val=1.0,
                    include_boundaries="both",
                )
            except Exception as e:
                raise ValueError(msg) from e
        else:
            raise ValueError(msg)

    cm = confusion_matrix(
        y_true,
        y_pred,
        sample_weight=sample_weight,
        labels=labels,
    )

    tn, fp, fn, tp = cm.ravel()
    support_pos = tp + fn
    support_neg = tn + fp
    pos_num = tp * support_neg
    pos_denom = fp * support_pos
    neg_num = fn * support_neg
    neg_denom = tn * support_pos

    # if `support_pos == 0`a division by zero will occur
    if support_pos == 0:
        msg = (
            "No samples of the positive class are present in `y_true`. "
            "`positive_likelihood_ratio` and `negative_likelihood_ratio` are both set "
            "to `np.nan`. Use the `replace_undefined_by` param to control this "
            "behavior. To suppress this warning or turn it into an error, see Python's "
            "`warnings` module and `warnings.catch_warnings()`."
        )
        warnings.warn(msg, UndefinedMetricWarning, stacklevel=2)
        positive_likelihood_ratio = np.nan
        negative_likelihood_ratio = np.nan

    # if `fp == 0`a division by zero will occur
    if fp == 0:
        if tp == 0:
            msg_beginning = (
                "No samples were predicted for the positive class and "
                "`positive_likelihood_ratio` is "
            )
        else:
            msg_beginning = "`positive_likelihood_ratio` is ill-defined and "
        msg_end = "set to `np.nan`. Use the `replace_undefined_by` param to "
        "control this behavior. To suppress this warning or turn it into an error, "
        "see Python's `warnings` module and `warnings.catch_warnings()`."
        warnings.warn(msg_beginning + msg_end, UndefinedMetricWarning, stacklevel=2)
        if isinstance(replace_undefined_by, float) and np.isnan(replace_undefined_by):
            positive_likelihood_ratio = replace_undefined_by
        else:
            # replace_undefined_by is a dict and
            # isinstance(replace_undefined_by.get("LR+", None), Real); this includes
            # `np.inf` and `np.nan`
            positive_likelihood_ratio = desired_lr_pos
    else:
        positive_likelihood_ratio = pos_num / pos_denom

    # if `tn == 0`a division by zero will occur
    if tn == 0:
        msg = (
            "`negative_likelihood_ratio` is ill-defined and set to `np.nan`. "
            "Use the `replace_undefined_by` param to control this behavior. To "
            "suppress this warning or turn it into an error, see Python's "
            "`warnings` module and `warnings.catch_warnings()`."
        )
        warnings.warn(msg, UndefinedMetricWarning, stacklevel=2)
        if isinstance(replace_undefined_by, float) and np.isnan(replace_undefined_by):
            negative_likelihood_ratio = replace_undefined_by
        else:
            # replace_undefined_by is a dict and
            # isinstance(replace_undefined_by.get("LR-", None), Real); this includes
            # `np.nan`
            negative_likelihood_ratio = desired_lr_neg
    else:
        negative_likelihood_ratio = neg_num / neg_denom

    return float(positive_likelihood_ratio), float(negative_likelihood_ratio)