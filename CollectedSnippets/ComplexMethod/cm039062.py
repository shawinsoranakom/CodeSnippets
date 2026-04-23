def _convert_to_logits(decision_values, eps=1e-12, xp=None):
    """Convert decision_function values to 2D and predict_proba values to logits.

    This function ensures that the output of `decision_function` is
    converted into a (n_samples, n_classes) array. For binary classification,
    each row contains logits for the negative and positive classes as (-x, x).

    If `predict_proba` is provided instead, it is converted into
    log-probabilities using `numpy.log`.

    Parameters
    ----------
    decision_values : array-like of shape (n_samples,) or (n_samples, 1) \
        or (n_samples, n_classes).

        The decision function values or probability estimates.
        - If shape is (n_samples,), converts to (n_samples, 2) with (-x, x).
        - If shape is (n_samples, 1), converts to (n_samples, 2) with (-x, x).
        - If shape is (n_samples, n_classes), returns unchanged.
        - For probability estimates, returns `numpy.log(decision_values + eps)`.

    eps : float
        Small positive value added to avoid log(0).

    Returns
    -------
    logits : ndarray of shape (n_samples, n_classes)
    """
    xp, _, device_ = get_namespace_and_device(decision_values, xp=xp)
    decision_values = check_array(
        decision_values, dtype=[xp.float64, xp.float32], ensure_2d=False
    )
    if (decision_values.ndim == 2) and (decision_values.shape[1] > 1):
        # Check if it is the output of predict_proba
        entries_zero_to_one = xp.all((decision_values >= 0) & (decision_values <= 1))
        # TODO: simplify once upstream issue is addressed
        # https://github.com/data-apis/array-api-extra/issues/478
        row_sums_to_one = xp.all(
            xpx.isclose(
                xp.sum(decision_values, axis=1),
                xp.asarray(1.0, device=device_, dtype=decision_values.dtype),
            )
        )

        if entries_zero_to_one and row_sums_to_one:
            logits = xp.log(decision_values + eps)
        else:
            logits = decision_values

    elif (decision_values.ndim == 2) and (decision_values.shape[1] == 1):
        logits = xp.concat([-decision_values, decision_values], axis=1)

    elif decision_values.ndim == 1:
        decision_values = xp.reshape(decision_values, (-1, 1))
        logits = xp.concat([-decision_values, decision_values], axis=1)

    return logits