def _check_targets(y_true, y_pred, sample_weight=None):
    """Check that y_true and y_pred belong to the same classification task.

    This converts multiclass or binary types to a common shape, and raises a
    ValueError for a mix of multilabel and multiclass targets, a mix of
    multilabel formats, for the presence of continuous-valued or multioutput
    targets, or for targets of different lengths.

    Column vectors are squeezed to 1d, while multilabel formats are returned
    as CSR sparse label indicators.

    Parameters
    ----------
    y_true : array-like

    y_pred : array-like

    sample_weight : array-like, default=None

    Returns
    -------
    type_true : one of {'multilabel-indicator', 'multiclass', 'binary'}
        The type of the true target data, as output by
        ``utils.multiclass.type_of_target``.

    y_true : array or indicator matrix

    y_pred : array or indicator matrix

    sample_weight : array or None
    """
    xp, _ = get_namespace(y_true, y_pred, sample_weight)
    check_consistent_length(y_true, y_pred, sample_weight)
    type_true = type_of_target(y_true, input_name="y_true")
    type_pred = type_of_target(y_pred, input_name="y_pred")
    for array in [y_true, y_pred]:
        if _num_samples(array) < 1:
            raise ValueError(
                "Found empty input array (e.g., `y_true` or `y_pred`) while a minimum "
                "of 1 sample is required."
            )
    if sample_weight is not None:
        sample_weight = _check_sample_weight(
            sample_weight, y_true, force_float_dtype=False
        )

    y_type = {type_true, type_pred}
    if y_type == {"binary", "multiclass"}:
        y_type = {"multiclass"}

    if len(y_type) > 1:
        raise ValueError(
            "Classification metrics can't handle a mix of {0} and {1} targets".format(
                type_true, type_pred
            )
        )

    # We can't have more than one value on y_type => The set is no more needed
    y_type = y_type.pop()

    # No metrics support "multiclass-multioutput" format
    if y_type not in ["binary", "multiclass", "multilabel-indicator"]:
        raise ValueError("{0} is not supported".format(y_type))

    if y_type in ["binary", "multiclass"]:
        try:
            y_true = column_or_1d(y_true, input_name="y_true")
            y_pred = column_or_1d(y_pred, input_name="y_pred")
        except TypeError as e:
            if "Sparse data was passed" in str(e):
                raise TypeError(
                    "Sparse input is only supported when targets are of multilabel type"
                ) from e
            else:
                raise

        xp, _ = get_namespace(y_true, y_pred)
        if y_type == "binary":
            try:
                unique_values = _union1d(y_true, y_pred, xp)
            except TypeError as e:
                # We expect y_true and y_pred to be of the same data type.
                # If `y_true` was provided to the classifier as strings,
                # `y_pred` given by the classifier will also be encoded with
                # strings. So we raise a meaningful error
                raise TypeError(
                    "Labels in y_true and y_pred should be of the same type. "
                    f"Got y_true={xp.unique(y_true)} and "
                    f"y_pred={xp.unique(y_pred)}. Make sure that the "
                    "predictions provided by the classifier coincides with "
                    "the true labels."
                ) from e
            if unique_values.shape[0] > 2:
                y_type = "multiclass"

    if y_type.startswith("multilabel"):
        if _is_numpy_namespace(xp):
            # XXX: do we really want to sparse-encode multilabel indicators when
            # they are passed as a dense arrays? This is not possible for array
            # API inputs in general hence we only do it for NumPy inputs. But even
            # for NumPy the usefulness is questionable.
            y_true = _align_api_if_sparse(csr_array(y_true))
            y_pred = _align_api_if_sparse(csr_array(y_pred))
        y_type = "multilabel-indicator"

    return y_type, y_true, y_pred, sample_weight