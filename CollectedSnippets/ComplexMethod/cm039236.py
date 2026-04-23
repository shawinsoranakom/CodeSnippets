def test_column_transformer_sparse_threshold():
    X_array = np.array([["a", "b"], ["A", "B"]], dtype=object).T
    # above data has sparsity of 4 / 8 = 0.5

    # apply threshold even if all sparse
    col_trans = ColumnTransformer(
        [("trans1", OneHotEncoder(), [0]), ("trans2", OneHotEncoder(), [1])],
        sparse_threshold=0.2,
    )
    res = col_trans.fit_transform(X_array)
    assert not sparse.issparse(res)
    assert not col_trans.sparse_output_

    # mixed -> sparsity of (4 + 2) / 8 = 0.75
    for thres in [0.75001, 1]:
        col_trans = ColumnTransformer(
            [
                ("trans1", OneHotEncoder(sparse_output=True), [0]),
                ("trans2", OneHotEncoder(sparse_output=False), [1]),
            ],
            sparse_threshold=thres,
        )
        res = col_trans.fit_transform(X_array)
        assert sparse.issparse(res)
        assert col_trans.sparse_output_

    for thres in [0.75, 0]:
        col_trans = ColumnTransformer(
            [
                ("trans1", OneHotEncoder(sparse_output=True), [0]),
                ("trans2", OneHotEncoder(sparse_output=False), [1]),
            ],
            sparse_threshold=thres,
        )
        res = col_trans.fit_transform(X_array)
        assert not sparse.issparse(res)
        assert not col_trans.sparse_output_

    # if nothing is sparse -> no sparse
    for thres in [0.33, 0, 1]:
        col_trans = ColumnTransformer(
            [
                ("trans1", OneHotEncoder(sparse_output=False), [0]),
                ("trans2", OneHotEncoder(sparse_output=False), [1]),
            ],
            sparse_threshold=thres,
        )
        res = col_trans.fit_transform(X_array)
        assert not sparse.issparse(res)
        assert not col_trans.sparse_output_