def test_sparse_output_multilabel_binarizer():
    # test input as iterable of iterables
    inputs = [
        lambda: [(2, 3), (1,), (1, 2)],
        lambda: ({2, 3}, {1}, {1, 2}),
        lambda: iter([iter((2, 3)), iter((1,)), {1, 2}]),
    ]
    indicator_mat = np.array([[0, 1, 1], [1, 0, 0], [1, 1, 0]])

    inverse = inputs[0]()
    for sparse_output in [True, False]:
        for inp in inputs:
            # With fit_transform
            mlb = MultiLabelBinarizer(sparse_output=sparse_output)
            got = mlb.fit_transform(inp())
            assert issparse(got) == sparse_output
            if sparse_output:
                # verify CSR assumption that indices and indptr have same dtype
                assert got.indices.dtype == got.indptr.dtype
                got = got.toarray()
            assert_array_equal(indicator_mat, got)
            assert_array_equal([1, 2, 3], mlb.classes_)
            assert mlb.inverse_transform(got) == inverse

            # With fit
            mlb = MultiLabelBinarizer(sparse_output=sparse_output)
            got = mlb.fit(inp()).transform(inp())
            assert issparse(got) == sparse_output
            if sparse_output:
                # verify CSR assumption that indices and indptr have same dtype
                assert got.indices.dtype == got.indptr.dtype
                got = got.toarray()
            assert_array_equal(indicator_mat, got)
            assert_array_equal([1, 2, 3], mlb.classes_)
            assert mlb.inverse_transform(got) == inverse