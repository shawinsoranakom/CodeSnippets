def test_validate_data_skip_check_array():
    """Check skip_check_array option of _validate_data."""

    pd = pytest.importorskip("pandas")
    iris = datasets.load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    y = pd.Series(iris.target)

    class NoOpTransformer(TransformerMixin, BaseEstimator):
        pass

    no_op = NoOpTransformer()
    X_np_out = validate_data(no_op, df, skip_check_array=False)
    assert isinstance(X_np_out, np.ndarray)
    assert_allclose(X_np_out, df.to_numpy())

    X_df_out = validate_data(no_op, df, skip_check_array=True)
    assert X_df_out is df

    y_np_out = validate_data(no_op, y=y, skip_check_array=False)
    assert isinstance(y_np_out, np.ndarray)
    assert_allclose(y_np_out, y.to_numpy())

    y_series_out = validate_data(no_op, y=y, skip_check_array=True)
    assert y_series_out is y

    X_np_out, y_np_out = validate_data(no_op, df, y, skip_check_array=False)
    assert isinstance(X_np_out, np.ndarray)
    assert_allclose(X_np_out, df.to_numpy())
    assert isinstance(y_np_out, np.ndarray)
    assert_allclose(y_np_out, y.to_numpy())

    X_df_out, y_series_out = validate_data(no_op, df, y, skip_check_array=True)
    assert X_df_out is df
    assert y_series_out is y

    msg = "Validation should be done on X, y or both."
    with pytest.raises(ValueError, match=msg):
        validate_data(no_op)