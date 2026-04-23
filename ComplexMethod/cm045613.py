def write(
    table: Table,
    postgres_settings: dict,
    table_name: str,
    *,
    max_batch_size: int | None = None,
    init_mode: Literal["default", "create_if_not_exists", "replace"] = "default",
    output_table_type: Literal["stream_of_changes", "snapshot"] = "stream_of_changes",
    primary_key: list[ColumnReference] | None = None,
    name: str | None = None,
    sort_by: Iterable[ColumnReference] | None = None,
    _external_diff_column: ColumnReference | None = None,
) -> None:
    """Writes ``table`` to a Postgres table. Two types of output tables are supported:
    **stream of changes** and **snapshot**.

    When using **stream of changes**, the output table contains a log of all changes that
    occurred in the Pathway table. In this case, it is expected to have two additional columns,
    ``time`` and ``diff``, both of integer type. ``time`` indicates the transactional
    minibatch time in which the row change occurred. ``diff`` can be either ``1`` for
    row insertion or ``-1`` for row deletion.

    When using **snapshot**, the set of columns in the output table matches the set of
    columns in the table you are writing. No additional columns are created.

    Args:
        table: Table to be written.
        postgres_settings: Components for the connection string for Postgres. The string is
            formed by joining key-value pairs from the given dictionary with spaces,
            with each pair formatted as `key=value`. Keys must be strings. Values can be
            of any type; if a value is not a string, it will be converted using Python's
            `str()` function.
        table_name: Name of the target table.
        max_batch_size: Maximum number of entries allowed to be committed within a
            single transaction.
        init_mode: "default": The default initialization mode;
            "create_if_not_exists": initializes the SQL writer by creating the necessary table
            if they do not already exist;
            "replace": Initializes the SQL writer by replacing any existing table.
        output_table_type: Defines how the output table manages its data. If set to ``"stream_of_changes"``
            (the default), the system outputs a stream of modifications to the target table.
            This stream includes two additional integer columns: ``time``, representing the computation
            minibatch, and ``diff``, indicating the type of change (``1`` for row addition and
            ``-1`` for row deletion). If set to ``"snapshot"``, the table maintains the current
            state of the data, updated atomically with each minibatch and ensuring that no partial
            minibatch updates are visible.
        primary_key: When using snapshot mode, one or more columns that form the primary
            key in the target Postgres table.
        name: A unique name for the connector. If provided, this name will be used in
            logs and monitoring dashboards.
        sort_by: If specified, the output will be sorted in ascending order based on the
            values of the given columns within each minibatch. When multiple columns are provided,
            the corresponding value tuples will be compared lexicographically.

    Returns:
        None

    Example:

    Consider there's a need to output a stream of updates from a table in Pathway to
    a table in Postgres. Let's see how this can be done with the connector.

    First of all, one needs to provide the required credentials for Postgres
    `connection string <https://www.postgresql.org/docs/current/libpq-connect.html>`_.
    While the connection string can include a wide variety of settings, such as SSL
    or connection timeouts, in this example we will keep it simple and provide the
    smallest example possible. Suppose that the database is running locally on the standard
    port 5432, that it has the name ``database`` and is accessible under the username
    ``user`` with a password ``pass``.

    It gives us the following content for the connection string:

    >>> connection_string_parts = {
    ...     "host": "localhost",
    ...     "port": "5432",
    ...     "dbname": "database",
    ...     "user": "user",
    ...     "password": "pass",
    ... }

    Now let's load a table, which we will output to the database:

    >>> import pathway as pw
    >>> t = pw.debug.table_from_markdown("age owner pet \\n 1 10 Alice 1 \\n 2 9 Bob 1 \\n 3 8 Alice 2")

    In order to output the table, we will need to create a new table in the database. The table
    would need to have all the columns that the output data has. Moreover it will need
    integer columns ``time`` and ``diff``, because these values are an essential part of the
    output. Finally, it is also a good idea to create the sequential primary key for
    our changes so that we know the updates' order.

    To sum things up, the table creation boils down to the following SQL command:

    .. code-block:: sql

        CREATE TABLE pets (
            id SERIAL PRIMARY KEY,
            time INTEGER NOT NULL,
            diff INTEGER NOT NULL,
            age INTEGER,
            owner TEXT,
            pet TEXT
        );

    Now, having done all the preparation, one can simply call:

    >>> pw.io.postgres.write(
    ...     t,
    ...     connection_string_parts,
    ...     "pets",
    ... )

    Consider another scenario: the ``pets`` table is updated and you need to keep only
    the latest record for each pet, identified by the ``pet`` field in this table.
    In this case, you need the output table type to be ``"snapshot"``. The table can be
    created automatically in the database if you set ``init_mode`` to ``"replace"`` or
    ``"create_if_not_exists"``. If you create it manually, the command can look like this:

    .. code-block:: sql

        CREATE TABLE pets (
            pet TEXT PRIMARY KEY,
            age INTEGER,
            owner TEXT
        );

    The primary key in the target table is the ``pet`` field. Therefore, the ``primary_key``
    parameter for the command should be ``[t.pet]``. You can write this table as follows:

    >>> pw.io.postgres.write(
    ...     t,
    ...     connection_string_parts,
    ...     "pets",
    ...     output_table_type="snapshot",
    ...     primary_key=[t.pet],
    ... )
    """

    tls = _build_tls_settings(postgres_settings)
    is_snapshot_mode = output_table_type == SNAPSHOT_OUTPUT_TABLE_TYPE
    data_storage = api.DataStorage(
        storage_type="postgres",
        connection_string=_connection_string_from_settings(postgres_settings),
        max_batch_size=max_batch_size,
        table_name=table_name,
        table_writer_init_mode=init_mode_from_str(init_mode),
        snapshot_maintenance_on_output=is_snapshot_mode,
        tls_settings=tls.settings,
    )

    if not is_snapshot_mode:
        if _external_diff_column is not None:
            raise ValueError(
                "_external_diff_column is only supported for the snapshot table type"
            )
        if primary_key is not None:
            raise ValueError(
                "primary_key can only be specified for the snapshot table type"
            )
    if (
        _external_diff_column is not None
        and _external_diff_column._column.dtype != dtype.INT
    ):
        raise ValueError("_external_diff_column can only have an integer type")

    external_diff_column_index = get_column_index(table, _external_diff_column)
    key_field_names = None
    if primary_key is not None:
        key_field_names = []
        for pkey_field in primary_key:
            key_field_names.append(pkey_field.name)
    data_format = api.DataFormat(
        format_type="identity",
        key_field_names=key_field_names,
        value_fields=_format_output_value_fields(table),
        table_name=table_name,
        external_diff_column_index=external_diff_column_index,
    )

    datasink_type = "snapshot" if is_snapshot_mode else "sink"
    table.to(
        datasink.GenericDataSink(
            data_storage,
            data_format,
            datasink_name=f"postgres.{datasink_type}",
            unique_name=name,
            sort_by=sort_by,
        )
    )