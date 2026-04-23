def static_table_from_pandas(
    scope,
    df: pd.DataFrame,
    connector_properties: ConnectorProperties | None = None,
    id_from: list[str] | None = None,
    schema: type[Schema] | None = None,
) -> Table:
    if schema is not None and id_from is not None:
        assert schema.primary_key_columns() == id_from

    if id_from is None and schema is not None:
        id_from = schema.primary_key_columns()

    ids = ids_from_pandas(df, connector_properties, id_from)
    column_types: dict[str, dt.DType] | None = None
    if schema is not None:
        column_types = dict(schema.__dtypes__)
        for column in PANDAS_PSEUDOCOLUMNS:
            column_types[column] = dt.INT

    data = {}
    for c in df.columns:
        type_from_schema = None if column_types is None else column_types[c]
        data[c] = [denumpify(v, type_from_schema) for _, v in df[c].items()]
        # df[c].items() is used because df[c].values is a numpy array
    ordinary_columns = [
        column for column in df.columns if column not in PANDAS_PSEUDOCOLUMNS
    ]
    if column_types:
        dtypes = [column_types[c].to_engine() for c in ordinary_columns]
    else:
        dtypes = [PathwayType.ANY] * len(ordinary_columns)

    if connector_properties is None:
        column_properties = []
        for c in ordinary_columns:
            dtype: type = int
            for v in data[c]:
                if v is not None:
                    dtype = type(v)
                    break
            column_properties.append(ColumnProperties(dtype=dt.wrap(dtype).to_engine()))
        connector_properties = ConnectorProperties(column_properties=column_properties)

    assert len(connector_properties.column_properties) == len(
        ordinary_columns
    ), "provided connector properties do not match the dataframe"

    input_data: CapturedStream = []
    for i, index in enumerate(df.index):
        key = ids[index]
        values = [data[c][i] for c in ordinary_columns]
        time = data[TIME_PSEUDOCOLUMN][i] if TIME_PSEUDOCOLUMN in data else 0
        diff = data[DIFF_PSEUDOCOLUMN][i] if DIFF_PSEUDOCOLUMN in data else 1
        if diff not in [-1, 1]:
            raise ValueError(f"Column {DIFF_PSEUDOCOLUMN} can only contain 1 and -1.")
        shard = data[SHARD_PSEUDOCOLUMN][i] if SHARD_PSEUDOCOLUMN in data else None
        input_row = DataRow(
            key, values, time=time, diff=diff, shard=shard, dtypes=dtypes
        )
        input_data.append(input_row)

    return scope.static_table(input_data, connector_properties)