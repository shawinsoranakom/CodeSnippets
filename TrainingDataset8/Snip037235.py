def _marshall_index(proto, index):
    """Marshall pandas.DataFrame index into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    index : Index or array-like
        Index to use for resulting frame.
        Will default to RangeIndex (0, 1, 2, ..., n) if no index is provided.

    """
    index = map(util._maybe_tuple_to_list, index.values)
    index_df = pd.DataFrame(index)
    proto.index = _dataframe_to_pybytes(index_df)