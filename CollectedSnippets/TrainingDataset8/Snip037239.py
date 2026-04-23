def _pybytes_to_dataframe(source):
    """Convert pybytes to pandas.DataFrame.

    Parameters
    ----------
    source : pybytes
        Will default to RangeIndex (0, 1, 2, ..., n) if no `index` or `columns` are provided.

    """
    reader = pa.RecordBatchStreamReader(source)
    return reader.read_pandas()