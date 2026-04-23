def update_confusion_matrix_variables(
    variables_to_update,
    y_true,
    y_pred,
    thresholds,
    top_k=None,
    class_id=None,
    sample_weight=None,
    multi_label=False,
    label_weights=None,
    thresholds_distributed_evenly=False,
):
    """Updates the given confusion matrix variables.

    For every pair of values in y_true and y_pred:

    true_positive: y_true == True and y_pred > thresholds
    false_negatives: y_true == True and y_pred <= thresholds
    true_negatives: y_true == False and y_pred <= thresholds
    false_positive: y_true == False and y_pred > thresholds

    The results will be weighted and added together. When multiple thresholds
    are provided, we will repeat the same for every threshold.

    For estimation of these metrics over a stream of data, the function creates
    an `update_op` operation that updates the given variables.

    If `sample_weight` is `None`, weights default to 1.
    Use weights of 0 to mask values.

    Args:
      variables_to_update: Dictionary with 'tp', 'fn', 'tn', 'fp' as valid keys
        and corresponding variables to update as values.
      y_true: A `Tensor` whose shape matches `y_pred`. Will be cast to `bool`.
      y_pred: A floating point `Tensor` of arbitrary shape and whose values are
        in the range `[0, 1]`.
      thresholds: A float value, float tensor, python list, or tuple of float
        thresholds in `[0, 1]`, or NEG_INF (used when top_k is set).
      top_k: Optional int, indicates that the positive labels should be limited
        to the top k predictions.
      class_id: Optional int, limits the prediction and labels to the class
        specified by this argument.
      sample_weight: Optional `Tensor` whose rank is either 0, or the same rank
        as `y_true`, and must be broadcastable to `y_true` (i.e., all dimensions
        must be either `1`, or the same as the corresponding `y_true`
        dimension).
      multi_label: Optional boolean indicating whether multidimensional
        prediction/labels should be treated as multilabel responses, or
        flattened into a single label. When True, the values of
        `variables_to_update` must have a second dimension equal to the number
        of labels in y_true and y_pred, and those tensors must not be
        RaggedTensors.
      label_weights: (optional) tensor of non-negative weights for multilabel
        data. The weights are applied when calculating TP, FP, FN, and TN
        without explicit multilabel handling (i.e. when the data is to be
        flattened).
      thresholds_distributed_evenly: Boolean, whether the thresholds are evenly
        distributed within the list. An optimized method will be used if this is
        the case. See _update_confusion_matrix_variables_optimized() for more
        details.

    Raises:
      ValueError: If `y_pred` and `y_true` have mismatched shapes, or if
        `sample_weight` is not `None` and its shape doesn't match `y_pred`, or
        if `variables_to_update` contains invalid keys.
    """
    if multi_label and label_weights is not None:
        raise ValueError(
            "`label_weights` for multilabel data should be handled "
            "outside of `update_confusion_matrix_variables` when "
            "`multi_label` is True."
        )
    if variables_to_update is None:
        return
    if not any(
        key for key in variables_to_update if key in list(ConfusionMatrix)
    ):
        raise ValueError(
            "Please provide at least one valid confusion matrix "
            "variable to update. Valid variable key options are: "
            f'"{list(ConfusionMatrix)}". '
            f'Received: "{variables_to_update.keys()}"'
        )

    variable_dtype = list(variables_to_update.values())[0].dtype

    y_true = ops.cast(y_true, dtype=variable_dtype)
    y_pred = ops.cast(y_pred, dtype=variable_dtype)

    if thresholds_distributed_evenly:
        # Check whether the thresholds has any leading or tailing epsilon added
        # for floating point imprecision. The leading and tailing threshold will
        # be handled bit differently as the corner case.  At this point,
        # thresholds should be a list/array with more than 2 items, and ranged
        # between [0, 1]. See is_evenly_distributed_thresholds() for more
        # details.
        thresholds_with_epsilon = thresholds[0] < 0.0 or thresholds[-1] > 1.0

    thresholds = ops.convert_to_tensor(thresholds, dtype=variable_dtype)
    num_thresholds = ops.shape(thresholds)[0]

    if multi_label:
        one_thresh = ops.equal(
            np.array(1, dtype="int32"),
            len(thresholds.shape),
        )
    else:
        one_thresh = np.array(True, dtype="bool")

    invalid_keys = [
        key for key in variables_to_update if key not in list(ConfusionMatrix)
    ]
    if invalid_keys:
        raise ValueError(
            f'Invalid keys: "{invalid_keys}". '
            f'Valid variable key options are: "{list(ConfusionMatrix)}"'
        )

    y_pred, y_true = squeeze_or_expand_to_same_rank(y_pred, y_true)
    if sample_weight is not None:
        sample_weight = ops.expand_dims(
            ops.cast(sample_weight, dtype=variable_dtype), axis=-1
        )
        _, sample_weight = squeeze_or_expand_to_same_rank(
            y_true, sample_weight, expand_rank_1=False
        )

    if top_k is not None:
        y_pred = _filter_top_k(y_pred, top_k)

    if class_id is not None:
        if len(y_pred.shape) == 1:
            raise ValueError(
                "When class_id is provided, y_pred must be a 2D array "
                "with shape (num_samples, num_classes), found shape: "
                f"{y_pred.shape}"
            )

        # Preserve dimension to match with sample_weight
        y_true = y_true[..., class_id, None]
        y_pred = y_pred[..., class_id, None]

    if thresholds_distributed_evenly:
        return _update_confusion_matrix_variables_optimized(
            variables_to_update,
            y_true,
            y_pred,
            thresholds,
            multi_label=multi_label,
            sample_weights=sample_weight,
            label_weights=label_weights,
            thresholds_with_epsilon=thresholds_with_epsilon,
        )

    if None in y_pred.shape:
        pred_shape = ops.shape(y_pred)
        num_predictions = pred_shape[0]
        if len(y_pred.shape) == 1:
            num_labels = 1
        else:
            num_labels = ops.cast(
                ops.prod(ops.array(pred_shape[1:]), axis=0), "int32"
            )
        thresh_label_tile = ops.where(one_thresh, num_labels, 1)
    else:
        pred_shape = ops.shape(y_pred)
        num_predictions = pred_shape[0]
        if len(y_pred.shape) == 1:
            num_labels = 1
        else:
            num_labels = np.prod(pred_shape[1:], axis=0).astype("int32")
        thresh_label_tile = np.where(one_thresh, num_labels, 1)

    # Reshape predictions and labels, adding a dim for thresholding.
    if multi_label:
        predictions_extra_dim = ops.expand_dims(y_pred, 0)
        labels_extra_dim = ops.expand_dims(ops.cast(y_true, dtype="bool"), 0)
    else:
        # Flatten predictions and labels when not multilabel.
        predictions_extra_dim = ops.reshape(y_pred, [1, -1])
        labels_extra_dim = ops.reshape(ops.cast(y_true, dtype="bool"), [1, -1])

    # Tile the thresholds for every prediction.
    if multi_label:
        thresh_pretile_shape = [num_thresholds, 1, -1]
        thresh_tiles = [1, num_predictions, thresh_label_tile]
        data_tiles = [num_thresholds, 1, 1]
    else:
        thresh_pretile_shape = [num_thresholds, -1]
        thresh_tiles = [1, num_predictions * num_labels]
        data_tiles = [num_thresholds, 1]

    thresh_tiled = ops.tile(
        ops.reshape(thresholds, thresh_pretile_shape), thresh_tiles
    )

    # Tile the predictions for every threshold.
    preds_tiled = ops.tile(predictions_extra_dim, data_tiles)

    # Compare predictions and threshold.
    pred_is_pos = ops.greater(preds_tiled, thresh_tiled)

    # Tile labels by number of thresholds
    label_is_pos = ops.tile(labels_extra_dim, data_tiles)

    if sample_weight is not None:
        sample_weight = ops.broadcast_to(
            ops.cast(sample_weight, dtype=y_pred.dtype), ops.shape(y_pred)
        )
        weights_tiled = ops.tile(
            ops.reshape(sample_weight, thresh_tiles), data_tiles
        )
    else:
        weights_tiled = None

    if label_weights is not None and not multi_label:
        label_weights = ops.expand_dims(label_weights, 0)
        label_weights = ops.broadcast_to(label_weights, ops.shape(y_pred))
        label_weights_tiled = ops.tile(
            ops.reshape(label_weights, thresh_tiles), data_tiles
        )
        if weights_tiled is None:
            weights_tiled = label_weights_tiled
        else:
            weights_tiled = ops.multiply(weights_tiled, label_weights_tiled)

    def weighted_assign_add(label, pred, weights, var):
        label_and_pred = ops.cast(ops.logical_and(label, pred), dtype=var.dtype)
        if weights is not None:
            label_and_pred *= ops.cast(weights, dtype=var.dtype)
        var.assign(var + ops.sum(label_and_pred, 1))

    loop_vars = {
        ConfusionMatrix.TRUE_POSITIVES: (label_is_pos, pred_is_pos),
    }
    update_tn = ConfusionMatrix.TRUE_NEGATIVES in variables_to_update
    update_fp = ConfusionMatrix.FALSE_POSITIVES in variables_to_update
    update_fn = ConfusionMatrix.FALSE_NEGATIVES in variables_to_update

    if update_fn or update_tn:
        pred_is_neg = ops.logical_not(pred_is_pos)
        loop_vars[ConfusionMatrix.FALSE_NEGATIVES] = (label_is_pos, pred_is_neg)

    if update_fp or update_tn:
        label_is_neg = ops.logical_not(label_is_pos)
        loop_vars[ConfusionMatrix.FALSE_POSITIVES] = (label_is_neg, pred_is_pos)
        if update_tn:
            loop_vars[ConfusionMatrix.TRUE_NEGATIVES] = (
                label_is_neg,
                pred_is_neg,
            )

    for matrix_cond, (label, pred) in loop_vars.items():
        if matrix_cond in variables_to_update:
            weighted_assign_add(
                label, pred, weights_tiled, variables_to_update[matrix_cond]
            )