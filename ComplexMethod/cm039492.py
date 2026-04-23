def label_ranking_average_precision_score(y_true, y_score, *, sample_weight=None):
    """Compute ranking-based average precision.

    Label ranking average precision (LRAP) is the average over each ground
    truth label assigned to each sample, of the ratio of true vs. total
    labels with lower score.

    This metric is used in multilabel ranking problem, where the goal
    is to give better rank to the labels associated to each sample.

    The obtained score is always strictly greater than 0 and
    the best value is 1.

    Read more in the :ref:`User Guide <label_ranking_average_precision>`.

    Parameters
    ----------
    y_true : {array-like, sparse matrix} of shape (n_samples, n_labels)
        True binary labels in :term:`label indicator format`.

    y_score : array-like of shape (n_samples, n_labels)
        Target scores, can either be probability estimates of the positive
        class or non-thresholded decision values (as returned by
        :term:`decision_function` on some classifiers).
        For :term:`decision_function` scores, values greater than or equal to
        zero should indicate the positive class.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

        .. versionadded:: 0.20

    Returns
    -------
    score : float
        Ranking-based average precision score.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.metrics import label_ranking_average_precision_score
    >>> y_true = np.array([[1, 0, 0], [0, 0, 1]])
    >>> y_score = np.array([[0.75, 0.5, 1], [1, 0.2, 0.1]])
    >>> label_ranking_average_precision_score(y_true, y_score)
    0.416
    """
    check_consistent_length(y_true, y_score, sample_weight)
    y_true = check_array(y_true, ensure_2d=False, accept_sparse="csr")
    y_score = check_array(y_score, ensure_2d=False)

    if y_true.shape != y_score.shape:
        raise ValueError("y_true and y_score have different shape")

    # Handle badly formatted array and the degenerate case with one label
    y_type = type_of_target(y_true, input_name="y_true")
    if y_type != "multilabel-indicator" and not (
        y_type == "binary" and y_true.ndim == 2
    ):
        raise ValueError("{0} format is not supported".format(y_type))

    if not issparse(y_true):
        y_true = csr_array(y_true)

    y_score = -y_score

    n_samples, n_labels = y_true.shape

    out = 0.0
    for i, (start, stop) in enumerate(zip(y_true.indptr, y_true.indptr[1:])):
        relevant = y_true.indices[start:stop]

        if relevant.size == 0 or relevant.size == n_labels:
            # If all labels are relevant or unrelevant, the score is also
            # equal to 1. The label ranking has no meaning.
            aux = 1.0
        else:
            scores_i = y_score[i]
            rank = rankdata(scores_i, "max")[relevant]
            L = rankdata(scores_i[relevant], "max")
            aux = (L / rank).mean()

        if sample_weight is not None:
            aux = aux * sample_weight[i]
        out += aux

    if sample_weight is None:
        out /= n_samples
    else:
        out /= np.sum(sample_weight)

    return float(out)