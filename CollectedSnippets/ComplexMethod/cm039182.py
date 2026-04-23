def dump_svmlight_file(
    X,
    y,
    f,
    *,
    zero_based=True,
    comment=None,
    query_id=None,
    multilabel=False,
):
    """Dump the dataset in svmlight / libsvm file format.

    This format is a text-based format, with one sample per line. It does
    not store zero valued features hence is suitable for sparse dataset.

    The first element of each line can be used to store a target variable
    to predict.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Training vectors, where `n_samples` is the number of samples and
        `n_features` is the number of features.

    y : {array-like, sparse matrix}, shape = (n_samples,) or (n_samples, n_labels)
        Target values. Class labels must be an
        integer or float, or array-like objects of integer or float for
        multilabel classifications.

    f : str or file-like in binary mode
        If string, specifies the path that will contain the data.
        If file-like, data will be written to f. f should be opened in binary
        mode.

    zero_based : bool, default=True
        Whether column indices should be written zero-based (True) or one-based
        (False).

    comment : str or bytes, default=None
        Comment to insert at the top of the file. This should be either a
        Unicode string, which will be encoded as UTF-8, or an ASCII byte
        string.
        If a comment is given, then it will be preceded by one that identifies
        the file as having been dumped by scikit-learn. Note that not all
        tools grok comments in SVMlight files.

    query_id : array-like of shape (n_samples,), default=None
        Array containing pairwise preference constraints (qid in svmlight
        format).

    multilabel : bool, default=False
        Samples may have several labels each (see
        https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multilabel.html).

        .. versionadded:: 0.17
           parameter `multilabel` to support multilabel datasets.

    Examples
    --------
    >>> from sklearn.datasets import dump_svmlight_file, make_classification
    >>> X, y = make_classification(random_state=0)
    >>> output_file = "my_dataset.svmlight"
    >>> dump_svmlight_file(X, y, output_file)  # doctest: +SKIP
    """
    if comment is not None:
        # Convert comment string to list of lines in UTF-8.
        # If a byte string is passed, then check whether it's ASCII;
        # if a user wants to get fancy, they'll have to decode themselves.
        if isinstance(comment, bytes):
            comment.decode("ascii")  # just for the exception
        else:
            comment = comment.encode("utf-8")
        if b"\0" in comment:
            raise ValueError("comment string contains NUL byte")

    yval = check_array(y, accept_sparse="csr", ensure_2d=False)
    if sp.issparse(yval):
        if yval.shape[1] != 1 and not multilabel:
            raise ValueError(
                "expected y of shape (n_samples, 1), got %r" % (yval.shape,)
            )
    else:
        if yval.ndim != 1 and not multilabel:
            raise ValueError("expected y of shape (n_samples,), got %r" % (yval.shape,))

    Xval = check_array(X, accept_sparse="csr")
    if Xval.shape[0] != yval.shape[0]:
        raise ValueError(
            "X.shape[0] and y.shape[0] should be the same, got %r and %r instead."
            % (Xval.shape[0], yval.shape[0])
        )

    # We had some issues with CSR matrices with unsorted indices (e.g. #1501),
    # so sort them here, but first make sure we don't modify the user's X.
    # TODO We can do this cheaper; sorted_indices copies the whole matrix.
    if yval is y and hasattr(yval, "sorted_indices"):
        y = yval.sorted_indices()
    else:
        y = yval
        if hasattr(y, "sort_indices"):
            y.sort_indices()

    if Xval is X and hasattr(Xval, "sorted_indices"):
        X = Xval.sorted_indices()
    else:
        X = Xval
        if hasattr(X, "sort_indices"):
            X.sort_indices()

    if query_id is None:
        # NOTE: query_id is passed to Cython functions using a fused type on query_id.
        # Yet as of Cython>=3.0, memory views can't be None otherwise the runtime
        # would not known which concrete implementation to dispatch the Python call to.
        # TODO: simplify interfaces and implementations in _svmlight_format_fast.pyx.
        query_id = np.array([], dtype=np.int32)
    else:
        query_id = np.asarray(query_id)
        if query_id.shape[0] != y.shape[0]:
            raise ValueError(
                "expected query_id of shape (n_samples,), got %r" % (query_id.shape,)
            )

    one_based = not zero_based

    if hasattr(f, "write"):
        _dump_svmlight(X, y, f, multilabel, one_based, comment, query_id)
    else:
        with open(f, "wb") as f:
            _dump_svmlight(X, y, f, multilabel, one_based, comment, query_id)