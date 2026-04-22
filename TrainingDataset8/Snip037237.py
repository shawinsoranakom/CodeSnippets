def _marshall_data(proto, data):
    """Marshall pandas.DataFrame data into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    df : pandas.DataFrame
        A dataframe to marshall.

    """
    df = pd.DataFrame(data)
    proto.data = _dataframe_to_pybytes(df)