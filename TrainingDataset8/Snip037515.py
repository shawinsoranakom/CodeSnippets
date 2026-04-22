def _marshall_table(pandas_table, proto_table) -> None:
    """Convert a sequence of 1D arrays into proto.Table.

    pandas_table - Sequence of 1D arrays which are AnyArray compatible (input).
    proto_table  - proto.Table (output)
    """
    for pandas_array in pandas_table:
        if len(pandas_array) == 0:
            continue
        _marshall_any_array(pandas_array, proto_table.cols.add())