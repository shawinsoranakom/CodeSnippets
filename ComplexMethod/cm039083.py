def label_binarize(y, *, classes, neg_label=0, pos_label=1, sparse_output=False):
    """Binarize labels in a one-vs-all fashion.

    Several regression and binary classification algorithms are
    available in scikit-learn. A simple way to extend these algorithms
    to the multi-class classification case is to use the so-called
    one-vs-all scheme.

    This function makes it possible to compute this transformation for a
    fixed set of class labels known ahead of time.

    Parameters
    ----------
    y : array-like or sparse matrix
        Sequence of integer labels or multilabel data to encode.

    classes : array-like of shape (n_classes,)
        Uniquely holds the label for each class.

    neg_label : int, default=0
        Value with which negative labels must be encoded.

    pos_label : int, default=1
        Value with which positive labels must be encoded.

    sparse_output : bool, default=False,
        Set to true if output binary array is desired in CSR sparse format.

    Returns
    -------
    Y : {ndarray, sparse matrix} of shape (n_samples, n_classes)
        Shape will be (n_samples, 1) for binary problems. Sparse matrix will
        be of CSR format.

    See Also
    --------
    LabelBinarizer : Class used to wrap the functionality of label_binarize and
        allow for fitting to classes independently of the transform operation.

    Examples
    --------
    >>> from sklearn.preprocessing import label_binarize
    >>> label_binarize([1, 6], classes=[1, 2, 4, 6])
    array([[1, 0, 0, 0],
           [0, 0, 0, 1]])

    The class ordering is preserved:

    >>> label_binarize([1, 6], classes=[1, 6, 4, 2])
    array([[1, 0, 0, 0],
           [0, 1, 0, 0]])

    Binary targets transform to a column vector

    >>> label_binarize(['yes', 'no', 'no', 'yes'], classes=['no', 'yes'])
    array([[1],
           [0],
           [0],
           [1]])
    """
    if not isinstance(y, list):
        # XXX Workaround that will be removed when list of list format is
        # dropped
        y = check_array(
            y, input_name="y", accept_sparse="csr", ensure_2d=False, dtype=None
        )
    else:
        if _num_samples(y) == 0:
            raise ValueError("y has 0 samples: %r" % y)
    if neg_label >= pos_label:
        raise ValueError(
            "neg_label={0} must be strictly less than pos_label={1}.".format(
                neg_label, pos_label
            )
        )

    if sparse_output and (pos_label == 0 or neg_label != 0):
        raise ValueError(
            "Sparse binarization is only supported with non "
            "zero pos_label and zero neg_label, got "
            "pos_label={0} and neg_label={1}"
            "".format(pos_label, neg_label)
        )

    # To account for pos_label == 0 in the dense case
    pos_switch = pos_label == 0
    if pos_switch:
        pos_label = -neg_label

    y_type = type_of_target(y)
    if "multioutput" in y_type:
        raise ValueError(
            "Multioutput target data is not supported with label binarization"
        )
    if y_type == "unknown":
        raise ValueError("The type of target data is not known")

    xp, is_array_api, device_ = get_namespace_and_device(y)

    if is_array_api and sparse_output and not _is_numpy_namespace(xp):
        raise ValueError(
            "`sparse_output=True` is not supported for array API "
            f"'namespace {xp.__name__}'. "
            "Use `sparse_output=False` to return a dense array instead."
        )

    try:
        classes = xp.asarray(classes, device=device_)
    except (ValueError, TypeError) as e:
        # `classes` contains an unsupported dtype for this namespace.
        # For example, attempting to create torch.tensor(["yes", "no"]) will fail.
        raise ValueError(
            f"`classes` contains unsupported dtype for array API namespace "
            f"'{xp.__name__}'."
        ) from e

    n_samples = y.shape[0] if hasattr(y, "shape") else len(y)
    n_classes = classes.shape[0]
    if hasattr(y, "dtype") and xp.isdtype(y.dtype, "integral"):
        int_dtype_ = y.dtype
    else:
        int_dtype_ = indexing_dtype(xp)

    if y_type == "binary":
        if n_classes == 1:
            if sparse_output:
                return _align_api_if_sparse(sp.csr_array((n_samples, 1), dtype=int))
            else:
                Y = xp.zeros((n_samples, 1), dtype=int_dtype_)
                Y += neg_label
                return Y
        elif n_classes >= 3:
            y_type = "multiclass"

    sorted_class = xp.sort(classes)
    if y_type == "multilabel-indicator":
        y_n_classes = y.shape[1] if hasattr(y, "shape") else len(y[0])
        if n_classes != y_n_classes:
            raise ValueError(
                "classes {0} mismatch with the labels {1} found in the data".format(
                    classes, unique_labels(y)
                )
            )

    if y_type in ("binary", "multiclass"):
        y = column_or_1d(y)

        # pick out the known labels from y
        y_in_classes = _isin(y, classes, xp=xp)
        y_seen = y[y_in_classes]
        indices = xp.searchsorted(sorted_class, y_seen)
        # cast `y_in_classes` to integer dtype for `xp.cumulative_sum`
        y_in_classes = xp.astype(y_in_classes, int_dtype_)
        indptr = xp.concat(
            (
                xp.asarray([0], device=device_),
                xp.cumulative_sum(y_in_classes, axis=0),
            )
        )
        data = xp.full_like(indices, pos_label)

        # Use NumPy to construct the sparse matrix of one-hot labels
        Y = sp.csr_array(
            (
                move_to(data, xp=np, device="cpu"),
                move_to(indices, xp=np, device="cpu"),
                move_to(indptr, xp=np, device="cpu"),
            ),
            shape=(n_samples, n_classes),
        )

        if not sparse_output:
            Y = xp.asarray(Y.toarray(), device=device_)

    elif y_type == "multilabel-indicator":
        if sparse_output:
            Y = sp.csr_array(y)
            if pos_label != 1:
                data = xp.full_like(Y.data, pos_label)
                Y.data = data
        else:
            if sp.issparse(y):
                y = y.toarray()

            Y = xp.asarray(y, device=device_, copy=True)
            if pos_label != 1:
                Y[Y != 0] = pos_label

    else:
        raise ValueError(
            "%s target data is not supported with label binarization" % y_type
        )

    if not sparse_output:
        if neg_label != 0:
            Y[Y == 0] = neg_label

        if pos_switch:
            Y[Y == pos_label] = 0

        Y = xp.astype(Y, int_dtype_, copy=False)
    else:
        Y.data = Y.data.astype(int, copy=False)

    # preserve label ordering
    if xp.any(classes != sorted_class):
        indices = xp.searchsorted(sorted_class, classes)
        Y = Y[:, indices]

    if y_type == "binary":
        if sparse_output:
            Y = Y[:, [-1]]
        else:
            Y = xp.reshape(Y[:, -1], (-1, 1))

    return _align_api_if_sparse(Y)