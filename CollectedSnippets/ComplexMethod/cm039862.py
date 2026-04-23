def is_multilabel(y):
    """Check if ``y`` is in a multilabel format.

    Parameters
    ----------
    y : ndarray of shape (n_samples,)
        Target values.

    Returns
    -------
    out : bool
        Return ``True``, if ``y`` is in a multilabel format, else ``False``.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils.multiclass import is_multilabel
    >>> is_multilabel([0, 1, 0, 1])
    False
    >>> is_multilabel([[1], [0, 2], []])
    False
    >>> is_multilabel(np.array([[1, 0], [0, 0]]))
    True
    >>> is_multilabel(np.array([[1], [0], [0]]))
    False
    >>> is_multilabel(np.array([[1, 0, 0]]))
    True
    """
    xp, is_array_api_compliant = get_namespace(y)
    if hasattr(y, "__array__") or isinstance(y, Sequence) or is_array_api_compliant:
        # DeprecationWarning will be replaced by ValueError, see NEP 34
        # https://numpy.org/neps/nep-0034-infer-dtype-is-object.html
        check_y_kwargs = dict(
            accept_sparse=True,
            allow_nd=True,
            ensure_all_finite=False,
            ensure_2d=False,
            ensure_min_samples=0,
            ensure_min_features=0,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error", VisibleDeprecationWarning)
            try:
                y = check_array(y, dtype=None, **check_y_kwargs)
            except (VisibleDeprecationWarning, ValueError) as e:
                if str(e).startswith("Complex data not supported"):
                    raise

                # dtype=object should be provided explicitly for ragged arrays,
                # see NEP 34
                y = check_array(y, dtype=object, **check_y_kwargs)

    if not (hasattr(y, "shape") and y.ndim == 2 and y.shape[1] > 1):
        return False

    if issparse(y):
        if y.format in ("dok", "lil"):
            y = y.tocsr()
        labels = xp.unique_values(y.data)
        return len(y.data) == 0 or (
            (labels.size == 1 or ((labels.size == 2) and (0 in labels)))
            and (y.dtype.kind in "biu" or _is_integral_float(labels))  # bool, int, uint
        )
    else:
        labels = cached_unique(y, xp=xp)

        return labels.shape[0] < 3 and (
            xp.isdtype(y.dtype, ("bool", "signed integer", "unsigned integer"))
            or _is_integral_float(labels)
        )