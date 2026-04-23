def test_pandas_adapter():
    """Check pandas adapter has expected behavior."""
    pd = pytest.importorskip("pandas")
    X_np = np.asarray([[1, 0, 3], [0, 0, 1]])
    columns = np.asarray(["f0", "f1", "f2"], dtype=object)
    index = np.asarray([1, 2])
    X_df_orig = pd.DataFrame([[1, 2], [1, 3]], index=index)
    X_ser_orig = pd.Series([2, 3], index=index)

    adapter = ADAPTERS_MANAGER.adapters["pandas"]
    X_container = adapter.create_container(X_np, X_df_orig, columns=lambda: columns)
    assert isinstance(X_container, pd.DataFrame)
    assert_array_equal(X_container.columns, columns)
    assert_array_equal(X_container.index, index)

    # use original index when the original is a series
    X_container = adapter.create_container(X_np, X_ser_orig, columns=lambda: columns)
    assert isinstance(X_container, pd.DataFrame)
    assert_array_equal(X_container.columns, columns)
    assert_array_equal(X_container.index, index)

    # Input dataframe's index does not change
    new_columns = np.asarray(["f0", "f1"], dtype=object)
    X_df = pd.DataFrame([[1, 2], [1, 3]], index=[10, 12])
    new_df = adapter.create_container(X_df, X_df_orig, columns=new_columns)
    assert_array_equal(new_df.columns, new_columns)
    assert_array_equal(new_df.index, X_df.index)

    assert adapter.is_supported_container(X_df)
    assert not adapter.is_supported_container(X_np)

    # adapter.update_columns updates the columns
    new_columns = np.array(["a", "c"], dtype=object)
    new_df = adapter.rename_columns(X_df, new_columns)
    assert_array_equal(new_df.columns, new_columns)

    # adapter.hstack stacks the dataframes horizontally.
    X_df_1 = pd.DataFrame([[1, 2, 5], [3, 4, 6]], columns=["a", "b", "e"])
    X_df_2 = pd.DataFrame([[4], [5]], columns=["c"])
    X_stacked = adapter.hstack([X_df_1, X_df_2])

    expected_df = pd.DataFrame(
        [[1, 2, 5, 4], [3, 4, 6, 5]], columns=["a", "b", "e", "c"]
    )
    pd.testing.assert_frame_equal(X_stacked, expected_df)

    # check that we update properly the columns even with duplicate column names
    # this use-case potentially happen when using ColumnTransformer
    # non-regression test for gh-28260
    X_df = pd.DataFrame([[1, 2], [1, 3]], columns=["a", "a"])
    new_columns = np.array(["x__a", "y__a"], dtype=object)
    new_df = adapter.rename_columns(X_df, new_columns)
    assert_array_equal(new_df.columns, new_columns)

    # check the behavior of the inplace parameter in `create_container`
    # we should trigger a copy
    X_df = pd.DataFrame([[1, 2], [1, 3]], index=index)
    X_output = adapter.create_container(X_df, X_df, columns=["a", "b"], inplace=False)
    assert X_output is not X_df
    assert list(X_df.columns) == [0, 1]
    assert list(X_output.columns) == ["a", "b"]

    # the operation is inplace
    X_df = pd.DataFrame([[1, 2], [1, 3]], index=index)
    X_output = adapter.create_container(X_df, X_df, columns=["a", "b"], inplace=True)
    assert X_output is X_df
    assert list(X_df.columns) == ["a", "b"]
    assert list(X_output.columns) == ["a", "b"]