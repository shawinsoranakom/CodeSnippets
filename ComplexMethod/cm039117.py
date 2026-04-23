def test_binarizer(constructor):
    X_ = np.array([[1, 0, 5], [2, 3, -1]])
    X = constructor(X_.copy())

    binarizer = Binarizer(threshold=2.0, copy=True)
    X_bin = toarray(binarizer.transform(X))
    assert np.sum(X_bin == 0) == 4
    assert np.sum(X_bin == 1) == 2
    X_bin = binarizer.transform(X)
    assert sparse.issparse(X) == sparse.issparse(X_bin)

    binarizer = Binarizer(copy=True).fit(X)
    X_bin = toarray(binarizer.transform(X))
    assert X_bin is not X
    assert np.sum(X_bin == 0) == 2
    assert np.sum(X_bin == 1) == 4

    binarizer = Binarizer(copy=True)
    X_bin = binarizer.transform(X)
    assert X_bin is not X
    X_bin = toarray(X_bin)
    assert np.sum(X_bin == 0) == 2
    assert np.sum(X_bin == 1) == 4

    binarizer = Binarizer(copy=False)
    X_bin = binarizer.transform(X)
    if constructor is not list:
        assert X_bin is X

    binarizer = Binarizer(copy=False)
    X_float = np.array([[1, 0, 5], [2, 3, -1]], dtype=np.float64)
    X_bin = binarizer.transform(X_float)
    if constructor is not list:
        assert X_bin is X_float

    X_bin = toarray(X_bin)
    assert np.sum(X_bin == 0) == 2
    assert np.sum(X_bin == 1) == 4

    binarizer = Binarizer(threshold=-0.5, copy=True)
    if constructor in (np.array, list):
        X = constructor(X_.copy())

        X_bin = toarray(binarizer.transform(X))
        assert np.sum(X_bin == 0) == 1
        assert np.sum(X_bin == 1) == 5
        X_bin = binarizer.transform(X)

    # Cannot use threshold < 0 for sparse
    if constructor in CSC_CONTAINERS:
        with pytest.raises(ValueError):
            binarizer.transform(constructor(X))