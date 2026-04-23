def bytes_to_data_frame(source: bytes) -> DataFrame:
    """Convert bytes to pandas.DataFrame.

    Parameters
    ----------
    source : bytes
        A bytes object to convert.

    """

    reader = pa.RecordBatchStreamReader(source)
    return reader.read_pandas()