def test_column_transformer_remainder():
    X_array = np.array([[0, 1, 2], [2, 4, 6]]).T

    X_res_first = np.array([0, 1, 2]).reshape(-1, 1)
    X_res_second = np.array([2, 4, 6]).reshape(-1, 1)
    X_res_both = X_array

    # default drop
    ct = ColumnTransformer([("trans1", Trans(), [0])])
    assert_array_equal(ct.fit_transform(X_array), X_res_first)
    assert_array_equal(ct.fit(X_array).transform(X_array), X_res_first)
    assert len(ct.transformers_) == 2
    assert ct.transformers_[-1][0] == "remainder"
    assert ct.transformers_[-1][1] == "drop"
    assert_array_equal(ct.transformers_[-1][2], [1])

    # specify passthrough
    ct = ColumnTransformer([("trans", Trans(), [0])], remainder="passthrough")
    assert_array_equal(ct.fit_transform(X_array), X_res_both)
    assert_array_equal(ct.fit(X_array).transform(X_array), X_res_both)
    assert len(ct.transformers_) == 2
    assert ct.transformers_[-1][0] == "remainder"
    assert isinstance(ct.transformers_[-1][1], FunctionTransformer)
    assert_array_equal(ct.transformers_[-1][2], [1])

    # column order is not preserved (passed through added to end)
    ct = ColumnTransformer([("trans1", Trans(), [1])], remainder="passthrough")
    assert_array_equal(ct.fit_transform(X_array), X_res_both[:, ::-1])
    assert_array_equal(ct.fit(X_array).transform(X_array), X_res_both[:, ::-1])
    assert len(ct.transformers_) == 2
    assert ct.transformers_[-1][0] == "remainder"
    assert isinstance(ct.transformers_[-1][1], FunctionTransformer)
    assert_array_equal(ct.transformers_[-1][2], [0])

    # passthrough when all actual transformers are skipped
    ct = ColumnTransformer([("trans1", "drop", [0])], remainder="passthrough")
    assert_array_equal(ct.fit_transform(X_array), X_res_second)
    assert_array_equal(ct.fit(X_array).transform(X_array), X_res_second)
    assert len(ct.transformers_) == 2
    assert ct.transformers_[-1][0] == "remainder"
    assert isinstance(ct.transformers_[-1][1], FunctionTransformer)
    assert_array_equal(ct.transformers_[-1][2], [1])

    # check default for make_column_transformer
    ct = make_column_transformer((Trans(), [0]))
    assert ct.remainder == "drop"