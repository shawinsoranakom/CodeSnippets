def _check_pos_label_consistency(pos_label, y_true):
    """Check if `pos_label` need to be specified or not.

    In binary classification, we fix `pos_label=1` if the labels are in the set
    {-1, 1} or {0, 1}. Otherwise, we raise an error asking to specify the
    `pos_label` parameters.

    Parameters
    ----------
    pos_label : int, float, bool, str or None
        The positive label.
    y_true : ndarray of shape (n_samples,)
        The target vector.

    Returns
    -------
    pos_label : int, float, bool or str
        If `pos_label` can be inferred, it will be returned.

    Raises
    ------
    ValueError
        In the case that `y_true` does not have label in {-1, 1} or {0, 1},
        it will raise a `ValueError`.
    """
    # ensure binary classification if pos_label is not specified
    # classes.dtype.kind in ('O', 'U', 'S') is required to avoid
    # triggering a FutureWarning by calling np.array_equal(a, b)
    # when elements in the two arrays are not comparable.
    if pos_label is None:
        # Compute classes only if pos_label is not specified:
        xp, _, device = get_namespace_and_device(y_true)
        classes = xp.unique_values(y_true)
        if (
            (_is_numpy_namespace(xp) and classes.dtype.kind in "OUS")
            or classes.shape[0] > 2
            or not (
                xp.all(classes == xp.asarray([0, 1], device=device))
                or xp.all(classes == xp.asarray([-1, 1], device=device))
                or xp.all(classes == xp.asarray([0], device=device))
                or xp.all(classes == xp.asarray([-1], device=device))
                or xp.all(classes == xp.asarray([1], device=device))
            )
        ):
            classes = move_to(classes, xp=np, device="cpu")
            classes_repr = ", ".join([repr(c) for c in classes.tolist()])
            raise ValueError(
                f"y_true takes value in {{{classes_repr}}} and pos_label is not "
                "specified: either make y_true take value in {0, 1} or "
                "{-1, 1} or pass pos_label explicitly."
            )
        pos_label = 1

    return pos_label