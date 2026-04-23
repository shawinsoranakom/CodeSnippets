def marshall(proto: ArrowProto, data: Data, default_uuid: Optional[str] = None) -> None:
    """Marshall pandas.DataFrame into an Arrow proto.

    Parameters
    ----------
    proto : proto.Arrow
        Output. The protobuf for Streamlit Arrow proto.

    data : pandas.DataFrame, pandas.Styler, pyarrow.Table, numpy.ndarray, pyspark.sql.DataFrame, snowflake.snowpark.DataFrame, Iterable, dict, or None
        Something that is or can be converted to a dataframe.

    default_uuid : Optional[str]
        If pandas.Styler UUID is not provided, this value will be used.
        This attribute is optional and only used for pandas.Styler, other elements
        (e.g. charts) can ignore it.

    """
    if type_util.is_pandas_styler(data):
        # default_uuid is a string only if the data is a `Styler`,
        # and `None` otherwise.
        assert isinstance(
            default_uuid, str
        ), "Default UUID must be a string for Styler data."
        _marshall_styler(proto, data, default_uuid)

    if isinstance(data, pa.Table):
        proto.data = type_util.pyarrow_table_to_bytes(data)
    else:
        df = type_util.convert_anything_to_df(data)
        proto.data = type_util.data_frame_to_bytes(df)