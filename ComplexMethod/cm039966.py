def test_polars_adapter():
    """Check Polars adapter has expected behavior."""
    pl = pytest.importorskip("polars")
    X_np = np.array([[1, 0, 3], [0, 0, 1]])
    columns = ["f1", "f2", "f3"]
    X_df_orig = pl.DataFrame(X_np, schema=columns, orient="row")

    adapter = ADAPTERS_MANAGER.adapters["polars"]
    X_container = adapter.create_container(X_np, X_df_orig, columns=lambda: columns)

    assert isinstance(X_container, pl.DataFrame)
    assert_array_equal(X_container.columns, columns)

    # Update columns with create_container
    new_columns = np.asarray(["a", "b", "c"], dtype=object)
    new_df = adapter.create_container(X_df_orig, X_df_orig, columns=new_columns)
    assert_array_equal(new_df.columns, new_columns)

    assert adapter.is_supported_container(X_df_orig)
    assert not adapter.is_supported_container(X_np)

    # adapter.update_columns updates the columns
    new_columns = np.array(["a", "c", "g"], dtype=object)
    new_df = adapter.rename_columns(X_df_orig, new_columns)
    assert_array_equal(new_df.columns, new_columns)

    # adapter.hstack stacks the dataframes horizontally.
    X_df_1 = pl.DataFrame([[1, 2, 5], [3, 4, 6]], schema=["a", "b", "e"], orient="row")
    X_df_2 = pl.DataFrame([[4], [5]], schema=["c"], orient="row")
    X_stacked = adapter.hstack([X_df_1, X_df_2])

    expected_df = pl.DataFrame(
        [[1, 2, 5, 4], [3, 4, 6, 5]], schema=["a", "b", "e", "c"], orient="row"
    )
    from polars.testing import assert_frame_equal

    assert_frame_equal(X_stacked, expected_df)

    # check the behavior of the inplace parameter in `create_container`
    # we should trigger a copy
    X_df = pl.DataFrame([[1, 2], [1, 3]], schema=["a", "b"], orient="row")
    X_output = adapter.create_container(X_df, X_df, columns=["c", "d"], inplace=False)
    assert X_output is not X_df
    assert list(X_df.columns) == ["a", "b"]
    assert list(X_output.columns) == ["c", "d"]

    # the operation is inplace
    X_df = pl.DataFrame([[1, 2], [1, 3]], schema=["a", "b"], orient="row")
    X_output = adapter.create_container(X_df, X_df, columns=["c", "d"], inplace=True)
    assert X_output is X_df
    assert list(X_df.columns) == ["c", "d"]
    assert list(X_output.columns) == ["c", "d"]