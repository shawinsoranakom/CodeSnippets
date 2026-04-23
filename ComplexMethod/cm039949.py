def test_check_array_pandas_dtype_casting():
    # test that data-frames with homogeneous dtype are not upcast
    pd = pytest.importorskip("pandas")
    X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float32)
    X_df = pd.DataFrame(X)
    assert check_array(X_df).dtype == np.float32
    assert check_array(X_df, dtype=FLOAT_DTYPES).dtype == np.float32

    X_df = X_df.astype({0: np.float16})
    assert_array_equal(X_df.dtypes, (np.float16, np.float32, np.float32))
    assert check_array(X_df).dtype == np.float32
    assert check_array(X_df, dtype=FLOAT_DTYPES).dtype == np.float32

    X_df = X_df.astype({0: np.int16})
    # float16, int16, float32 casts to float32
    assert check_array(X_df).dtype == np.float32
    assert check_array(X_df, dtype=FLOAT_DTYPES).dtype == np.float32

    X_df = X_df.astype({2: np.float16})
    # float16, int16, float16 casts to float32
    assert check_array(X_df).dtype == np.float32
    assert check_array(X_df, dtype=FLOAT_DTYPES).dtype == np.float32

    X_df = X_df.astype(np.int16)
    assert check_array(X_df).dtype == np.int16
    # we're not using upcasting rules for determining
    # the target type yet, so we cast to the default of float64
    assert check_array(X_df, dtype=FLOAT_DTYPES).dtype == np.float64

    # check that we handle pandas dtypes in a semi-reasonable way
    # this is actually tricky because we can't really know that this
    # should be integer ahead of converting it.
    cat_df = pd.DataFrame({"cat_col": pd.Categorical([1, 2, 3])})
    assert check_array(cat_df).dtype == np.int64
    assert check_array(cat_df, dtype=FLOAT_DTYPES).dtype == np.float64