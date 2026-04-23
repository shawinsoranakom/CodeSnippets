def _check_set_wise_labels(y_true, y_pred, average, labels, pos_label):
    """Validation associated with set-wise metrics.

    Returns identified labels.
    """
    average_options = (None, "micro", "macro", "weighted", "samples")
    if average not in average_options and average != "binary":
        raise ValueError("average has to be one of " + str(average_options))

    y_true, y_pred = attach_unique(y_true, y_pred)
    y_type, y_true, y_pred, _ = _check_targets(y_true, y_pred)
    present_labels = unique_labels(y_true, y_pred)
    if average == "binary":
        if y_type == "binary":
            if pos_label not in present_labels:
                if len(present_labels) >= 2:
                    raise ValueError(
                        f"pos_label={pos_label} is not a valid label. It "
                        f"should be one of {present_labels}"
                    )
            labels = [pos_label]
        else:
            average_options = list(average_options)
            if y_type == "multiclass":
                average_options.remove("samples")
            raise ValueError(
                "Target is %s but average='binary'. Please "
                "choose another average setting, one of %r." % (y_type, average_options)
            )
    elif pos_label not in (None, 1):
        warnings.warn(
            "Note that pos_label (set to %r) is ignored when "
            "average != 'binary' (got %r). You may use "
            "labels=[pos_label] to specify a single positive class."
            % (pos_label, average),
            UserWarning,
        )
    return labels