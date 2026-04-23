def _get_feature_names(X):
    """Get feature names from X.

    Support for other array containers should place its implementation here.

    Parameters
    ----------
    X : {ndarray, dataframe} of shape (n_samples, n_features)
        Array container to extract feature names.

        - pandas dataframe : The columns will be considered to be feature
          names. If the dataframe contains non-string feature names, `None` is
          returned.
        - All other array containers will return `None`.

    Returns
    -------
    names: ndarray or None
        Feature names of `X`. Unrecognized array containers will return `None`.
    """
    feature_names = None

    # extract feature names for support array containers
    if is_pandas_df(X):
        # Make sure we can inspect columns names from pandas, even with
        # versions too old to expose a working implementation of
        # __dataframe__.column_names() and avoid introducing any
        # additional copy.
        # TODO: remove the pandas-specific branch once the minimum supported
        # version of pandas has a working implementation of
        # __dataframe__.column_names() that is guaranteed to not introduce any
        # additional copy of the data without having to impose allow_copy=False
        # that could fail with other libraries. Note: in the longer term, we
        # could decide to instead rely on the __dataframe_namespace__ API once
        # adopted by our minimally supported pandas version.
        feature_names = np.asarray(X.columns, dtype=object)
    elif hasattr(X, "__dataframe__"):
        df_protocol = X.__dataframe__()
        feature_names = np.asarray(list(df_protocol.column_names()), dtype=object)

    if feature_names is None or len(feature_names) == 0:
        return

    types = sorted(t.__qualname__ for t in set(type(v) for v in feature_names))

    # mixed type of string and non-string is not supported
    if len(types) > 1 and "str" in types:
        raise TypeError(
            "Feature names are only supported if all input features have string names, "
            f"but your input has {types} as feature name / column name types. "
            "If you want feature names to be stored and validated, you must convert "
            "them all to strings, by using X.columns = X.columns.astype(str) for "
            "example. Otherwise you can remove feature / column names from your input "
            "data, or convert them all to a non-string data type."
        )

    # Only feature names of all strings are supported
    if len(types) == 1 and types[0] == "str":
        return feature_names