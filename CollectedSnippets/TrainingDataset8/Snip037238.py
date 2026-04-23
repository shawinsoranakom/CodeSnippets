def arrow_proto_to_dataframe(proto):
    """Convert ArrowTable proto to pandas.DataFrame.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. pandas.DataFrame

    """
    data = _pybytes_to_dataframe(proto.data)
    index = _pybytes_to_dataframe(proto.index)
    columns = _pybytes_to_dataframe(proto.columns)

    return pd.DataFrame(
        data.values, index=index.values.T.tolist(), columns=columns.values.T.tolist()
    )