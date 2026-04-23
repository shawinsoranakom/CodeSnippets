def _validate_binary_probabilistic_prediction(y_true, y_prob, sample_weight, pos_label):
    r"""Convert y_true and y_prob in binary classification to shape (n_samples, 2)

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        True labels.

    y_prob : array-like of shape (n_samples,)
        Probabilities of the positive class.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    pos_label : int, float, bool or str, default=None
        Label of the positive class. If None, `pos_label` will be inferred
        in the following manner:

        * if `y_true` in {-1, 1} or {0, 1}, `pos_label` defaults to 1;
        * else if `y_true` contains string, an error will be raised and
          `pos_label` should be explicitly specified;
        * otherwise, `pos_label` defaults to the greater label,
          i.e. `np.unique(y_true)[-1]`.

    Returns
    -------
    transformed_labels : array of shape (n_samples, 2)

    y_prob : array of shape (n_samples, 2)
    """
    # sanity checks on y_true and y_prob
    y_true = column_or_1d(y_true)
    y_prob = column_or_1d(y_prob)

    assert_all_finite(y_true)
    assert_all_finite(y_prob)

    check_consistent_length(y_prob, y_true, sample_weight)
    if sample_weight is not None:
        _check_sample_weight(sample_weight, y_prob, force_float_dtype=False)

    y_type = type_of_target(y_true, input_name="y_true")
    if y_type != "binary":
        raise ValueError(
            f"The type of the target inferred from y_true is {y_type} but should be "
            "binary according to the shape of y_prob."
        )

    xp, _, device_ = get_namespace_and_device(y_prob)
    if xp.max(y_prob) > 1:
        raise ValueError(f"y_prob contains values greater than 1: {xp.max(y_prob)}")
    if xp.min(y_prob) < 0:
        raise ValueError(f"y_prob contains values less than 0: {xp.min(y_prob)}")

    # check that pos_label is consistent with y_true
    try:
        pos_label = _check_pos_label_consistency(pos_label, y_true)
    except ValueError:
        xp_y_true, _ = get_namespace(y_true)
        classes = xp_y_true.unique_values(y_true)
        # For backward compatibility, if classes are not string then
        # `pos_label` will correspond to the greater label.
        if not (_is_numpy_namespace(xp_y_true) and classes.dtype.kind in "OUS"):
            pos_label = classes[-1]
        else:
            raise

    # convert (n_samples,) to (n_samples, 2) shape
    transformed_labels = _one_hot_encoding_binary_target(
        y_true=y_true, pos_label=pos_label, target_xp=xp, target_device=device_
    )
    y_prob = xp.stack((1 - y_prob, y_prob), axis=1)

    return transformed_labels, y_prob