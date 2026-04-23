def marshall_data_frame(data: Data, proto_df: DataFrameProto) -> None:
    """Convert a pandas.DataFrame into a proto.DataFrame.

    Parameters
    ----------
    data : pandas.DataFrame, numpy.ndarray, Iterable, dict, DataFrame, Styler, or None
        Something that is or can be converted to a dataframe.

    proto_df : proto.DataFrame
        Output. The protobuf for a Streamlit DataFrame proto.
    """
    if isinstance(data, pa.Table):
        raise errors.StreamlitAPIException(
            """
pyarrow tables are not supported  by Streamlit's legacy DataFrame serialization (i.e. with `config.dataFrameSerialization = "legacy"`).

To be able to use pyarrow tables, please enable pyarrow by changing the config setting,
`config.dataFrameSerialization = "arrow"`
"""
        )
    df = type_util.convert_anything_to_df(data)

    # Convert df into an iterable of columns (each of type Series).
    df_data = (df.iloc[:, col] for col in range(len(df.columns)))

    _marshall_table(df_data, proto_df.data)
    _marshall_index(df.columns, proto_df.columns)
    _marshall_index(df.index, proto_df.index)

    styler = data if type_util.is_pandas_styler(data) else None
    _marshall_styles(proto_df.style, df, styler)