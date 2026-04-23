def test_check_array():
    # accept_sparse == False
    # raise error on sparse inputs
    X = [[1, 2], [3, 4]]
    X_csr = sp.csr_array(X)
    with pytest.raises(TypeError):
        check_array(X_csr)

    # ensure_2d=False
    X_array = check_array([0, 1, 2], ensure_2d=False)
    assert X_array.ndim == 1
    # ensure_2d=True with 1d array
    with pytest.raises(ValueError, match="Expected 2D array, got 1D array instead"):
        check_array([0, 1, 2], ensure_2d=True)

    # ensure_2d=True with scalar array
    with pytest.raises(ValueError, match="Expected 2D array, got scalar array instead"):
        check_array(10, ensure_2d=True)

    # ensure_2d=True with 1d sparse array
    if hasattr(sp, "csr_array"):
        sparse_row = next(iter(sp.csr_array(X)))
        if sparse_row.ndim == 1:
            # In scipy 1.14 and later, sparse row is 1D while it was 2D before.
            with pytest.raises(ValueError, match="Expected 2D input, got"):
                check_array(sparse_row, accept_sparse=True, ensure_2d=True)

    # don't allow ndim > 3
    X_ndim = np.arange(8).reshape(2, 2, 2)
    with pytest.raises(ValueError):
        check_array(X_ndim)
    check_array(X_ndim, allow_nd=True)  # doesn't raise

    # dtype and order enforcement.
    X_C = np.arange(4).reshape(2, 2).copy("C")
    X_F = X_C.copy("F")
    X_int = X_C.astype(int)
    X_float = X_C.astype(float)
    Xs = [X_C, X_F, X_int, X_float]
    dtypes = [np.int32, int, float, np.float32, None, bool, object]
    orders = ["C", "F", None]
    copys = [True, False]

    for X, dtype, order, copy in product(Xs, dtypes, orders, copys):
        X_checked = check_array(X, dtype=dtype, order=order, copy=copy)
        if dtype is not None:
            assert X_checked.dtype == dtype
        else:
            assert X_checked.dtype == X.dtype
        if order == "C":
            assert X_checked.flags["C_CONTIGUOUS"]
            assert not X_checked.flags["F_CONTIGUOUS"]
        elif order == "F":
            assert X_checked.flags["F_CONTIGUOUS"]
            assert not X_checked.flags["C_CONTIGUOUS"]
        if copy:
            assert X is not X_checked
        else:
            # doesn't copy if it was already good
            if (
                X.dtype == X_checked.dtype
                and X_checked.flags["C_CONTIGUOUS"] == X.flags["C_CONTIGUOUS"]
                and X_checked.flags["F_CONTIGUOUS"] == X.flags["F_CONTIGUOUS"]
            ):
                assert X is X_checked

    # allowed sparse != None

    # try different type of sparse format
    Xs = []
    Xs.extend(
        [
            sparse_container(X_C)
            for sparse_container in CSR_CONTAINERS
            + CSC_CONTAINERS
            + COO_CONTAINERS
            + DOK_CONTAINERS
        ]
    )
    Xs.extend([Xs[0].astype(np.int64), Xs[0].astype(np.float64)])

    accept_sparses = [["csr", "coo"], ["coo", "dok"]]
    # scipy sparse matrices do not support the object dtype so
    # this dtype is skipped in this loop
    non_object_dtypes = [dt for dt in dtypes if dt is not object]
    for X, dtype, accept_sparse, copy in product(
        Xs, non_object_dtypes, accept_sparses, copys
    ):
        X_checked = check_array(X, dtype=dtype, accept_sparse=accept_sparse, copy=copy)
        if dtype is not None:
            assert X_checked.dtype == dtype
        else:
            assert X_checked.dtype == X.dtype
        if X.format in accept_sparse:
            # no change if allowed
            assert X.format == X_checked.format
        else:
            # got converted
            assert X_checked.format == accept_sparse[0]
        if copy:
            assert X is not X_checked
        else:
            # doesn't copy if it was already good
            if X.dtype == X_checked.dtype and X.format == X_checked.format:
                assert X is X_checked

    # other input formats
    # convert lists to arrays
    X_dense = check_array([[1, 2], [3, 4]])
    assert isinstance(X_dense, np.ndarray)
    # raise on too deep lists
    with pytest.raises(ValueError):
        check_array(X_ndim.tolist())
    check_array(X_ndim.tolist(), allow_nd=True)  # doesn't raise

    # convert weird stuff to arrays
    X_no_array = _NotAnArray(X_dense)
    result = check_array(X_no_array)
    assert isinstance(result, np.ndarray)

    # check negative values when ensure_non_negative=True
    X_neg = check_array([[1, 2], [-3, 4]])
    err_msg = "Negative values in data passed to X in RandomForestRegressor"
    with pytest.raises(ValueError, match=err_msg):
        check_array(
            X_neg,
            ensure_non_negative=True,
            input_name="X",
            estimator=RandomForestRegressor(),
        )