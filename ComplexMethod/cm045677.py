def _type_converter(series: pd.Series) -> dt.DType:
    if series.empty:
        return dt.ANY

    if series.apply(lambda x: isinstance(x, dict)).all():
        return dt.JSON
    if series.apply(lambda x: isinstance(x, (tuple, list))).all():
        proposed_len = len(series[0])
        if (series.apply(lambda x: len(x) == proposed_len)).all():
            dtypes = [
                _type_converter(series.apply(lambda x: x[i]))
                for i in range(proposed_len)
            ]
            return dt.Tuple(*dtypes)
        else:
            exploded = pd.Series([x for element in series for x in element])
            to_wrap = _type_converter(exploded)
            return dt.List(to_wrap)
    if (series.isna() | series.isnull()).all():
        return dt.NONE
    if (series.apply(lambda x: isinstance(x, np.ndarray))).all():
        if series.apply(lambda x: np.issubdtype(x.dtype, np.integer)).all():
            wrapped = dt.INT
        elif series.apply(lambda x: np.issubdtype(x.dtype, np.floating)).all():
            wrapped = dt.FLOAT
        else:
            wrapped = dt.ANY
        n_dim: int | None = len(series[0].shape)
        if not series.apply(lambda x: len(x.shape) == n_dim).all():
            n_dim = None

        return dt.Array(n_dim=n_dim, wrapped=wrapped)
    if pd.api.types.is_integer_dtype(series.dtype):
        ret_type: dt.DType = dt.INT
    elif pd.api.types.is_float_dtype(series.dtype):
        ret_type = dt.FLOAT
    elif pd.api.types.is_bool_dtype(series.dtype):
        ret_type = dt.BOOL
    elif pd.api.types.is_string_dtype(series.dtype):
        ret_type = dt.STR
    elif pd.api.types.is_datetime64_ns_dtype(series.dtype):
        if series.dt.tz is None:
            ret_type = dt.DATE_TIME_NAIVE
        else:
            ret_type = dt.DATE_TIME_UTC
    elif pd.api.types.is_timedelta64_dtype(series.dtype):
        ret_type = dt.DURATION
    elif pd.api.types.is_object_dtype(series.dtype):
        ret_type = dt.ANY
    else:
        ret_type = dt.ANY
    if series.isna().any() or series.isnull().any():
        return dt.Optional(ret_type)
    else:
        return ret_type