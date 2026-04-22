def _marshall_columns(proto, columns):
    """Marshall pandas.DataFrame columns into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    columns : Index or array-like
        Column labels to use for resulting frame.
        Will default to RangeIndex (0, 1, 2, ..., n) if no column labels are provided.

    """
    columns = map(util._maybe_tuple_to_list, columns.values)
    columns_df = pd.DataFrame(columns)
    proto.columns = _dataframe_to_pybytes(columns_df)