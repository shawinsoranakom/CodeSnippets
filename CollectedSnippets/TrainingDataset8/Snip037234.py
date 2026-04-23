def _dataframe_to_pybytes(df):
    """Convert pandas.DataFrame to pybytes.

    Parameters
    ----------
    df : pandas.DataFrame
        A dataframe to convert.

    """
    table = pa.Table.from_pandas(df)
    sink = pa.BufferOutputStream()
    writer = pa.RecordBatchStreamWriter(sink, table.schema)
    writer.write_table(table)
    writer.close()
    return sink.getvalue().to_pybytes()