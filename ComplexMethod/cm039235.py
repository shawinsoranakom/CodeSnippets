def test_column_transformer_empty_columns(pandas, column_selection, callable_column):
    # test case that ensures that the column transformer does also work when
    # a given transformer doesn't have any columns to work on
    X_array = np.array([[0, 1, 2], [2, 4, 6]]).T
    X_res_both = X_array

    if pandas:
        pd = pytest.importorskip("pandas")
        X = pd.DataFrame(X_array, columns=["first", "second"])
    else:
        X = X_array

    if callable_column:
        column = lambda X: column_selection
    else:
        column = column_selection

    ct = ColumnTransformer(
        [("trans1", Trans(), [0, 1]), ("trans2", TransRaise(), column)]
    )
    assert_array_equal(ct.fit_transform(X), X_res_both)
    assert_array_equal(ct.fit(X).transform(X), X_res_both)
    assert len(ct.transformers_) == 2
    assert isinstance(ct.transformers_[1][1], TransRaise)

    ct = ColumnTransformer(
        [("trans1", TransRaise(), column), ("trans2", Trans(), [0, 1])]
    )
    assert_array_equal(ct.fit_transform(X), X_res_both)
    assert_array_equal(ct.fit(X).transform(X), X_res_both)
    assert len(ct.transformers_) == 2
    assert isinstance(ct.transformers_[0][1], TransRaise)

    ct = ColumnTransformer([("trans", TransRaise(), column)], remainder="passthrough")
    assert_array_equal(ct.fit_transform(X), X_res_both)
    assert_array_equal(ct.fit(X).transform(X), X_res_both)
    assert len(ct.transformers_) == 2  # including remainder
    assert isinstance(ct.transformers_[0][1], TransRaise)

    fixture = np.array([[], [], []])
    ct = ColumnTransformer([("trans", TransRaise(), column)], remainder="drop")
    assert_array_equal(ct.fit_transform(X), fixture)
    assert_array_equal(ct.fit(X).transform(X), fixture)
    assert len(ct.transformers_) == 2  # including remainder
    assert isinstance(ct.transformers_[0][1], TransRaise)