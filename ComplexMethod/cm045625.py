def table_from_pandas(
    df: pd.DataFrame,
    id_from: list[str] | None = None,
    unsafe_trusted_ids: bool = False,
    schema: type[Schema] | None = None,
    _stacklevel: int = 1,
    _new_universe: bool = False,
) -> Table:
    """A function for creating a table from a pandas DataFrame. If it contains a special
    column ``__time__``, rows will be split into batches with timestamps from the column.
    A special column ``__diff__`` can be used to set an event type - with ``1`` treated
    as inserting the row and ``-1`` as removing it.
    """
    if id_from is not None and schema is not None:
        raise ValueError("parameters `schema` and `id_from` are mutually exclusive")

    ordinary_columns_names = [
        column for column in df.columns if column not in api.PANDAS_PSEUDOCOLUMNS
    ]
    if schema is None:
        schema = schema_from_pandas(
            df, id_from=id_from, exclude_columns=api.PANDAS_PSEUDOCOLUMNS
        )
    elif set(ordinary_columns_names) != set(schema.column_names()):
        raise ValueError("schema does not match given dataframe")

    _validate_dataframe(df, stacklevel=_stacklevel + 4)

    if id_from is None and schema is not None:
        id_from = schema.primary_key_columns()

    if id_from is None:
        ids_df = pd.DataFrame({"id": df.index})
        ids_df.index = df.index
    else:
        ids_df = df[id_from].copy()

    for column in api.PANDAS_PSEUDOCOLUMNS:
        if column in df.columns:
            ids_df[column] = df[column]

    as_hashes = [fingerprint(x) for x in ids_df.to_dict(orient="records")]
    key = fingerprint((unsafe_trusted_ids, sorted(as_hashes)))

    ret: Table = table_from_datasource(
        PandasDataSource(
            schema=schema,
            data=df.copy(),
            data_source_options=DataSourceOptions(
                unsafe_trusted_ids=unsafe_trusted_ids,
            ),
        )
    )
    from pathway.internals.parse_graph import G

    if not _new_universe:
        if key in G.static_tables_cache:
            ret = ret.with_universe_of(G.static_tables_cache[key])
        else:
            G.static_tables_cache[key] = ret

    return ret