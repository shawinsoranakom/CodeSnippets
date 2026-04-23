def write(
    table: Table,
    uri: str | PathLike,
    *,
    s3_connection_settings: (
        AwsS3Settings | MinIOSettings | WasabiS3Settings | DigitalOceanS3Settings | None
    ) = None,
    partition_columns: Iterable[ColumnReference] | None = None,
    min_commit_frequency: int | None = 60_000,
    name: str | None = None,
    sort_by: Iterable[ColumnReference] | None = None,
    output_table_type: Literal["stream_of_changes", "snapshot"] = "stream_of_changes",
    table_optimizer: TableOptimizer | None = None,
) -> None:
    """
    Writes the stream of changes from ``table`` into `Delta Lake <https://delta.io/>_` data
    storage at the location specified by ``uri``. Supported storage types are S3 and the
    local filesystem.

    The storage type is determined by the URI: paths starting with ``s3://`` or ``s3a://``
    are for S3 storage, while all other paths use the filesystem.

    If the specified storage location doesn't exist, it will be created. The schema of
    the new table is inferred from the ``table``'s schema. Additionally, when the connector
    creates a table, its Pathway schema is stored in the column metadata. This allows the
    table to be read using ``pw.io.deltalake.read`` without explicitly specifying a ``schema``.

    Args:
        table: Table to be written.
        uri: URI of the target Delta Lake.
        s3_connection_settings: Configuration for S3 credentials when using S3 storage.
            In addition to the access key and secret access key, you can specify a custom
            endpoint, which is necessary for buckets hosted outside of Amazon AWS. If the
            custom endpoint is left blank, the authorized user's credentials for S3 will
            be used.
        partition_columns: Partition columns for the table. Used if the table is created by
            Pathway.
        min_commit_frequency: Specifies the minimum time interval between two data commits in
            storage, measured in milliseconds. If set to None, finalized minibatches will
            be committed as soon as possible. Keep in mind that each commit in Delta Lake
            creates a new file and writes an entry in the transaction log. Therefore, it
            is advisable to limit the frequency of commits to reduce the overhead of
            processing the resulting table. Note that to further optimize performance and
            reduce the number of chunks in the table, you can use \
`vacuum <https://docs.delta.io/latest/delta-utility.html#remove-files-no-longer-referenced-by-a-delta-table>`_
            or \
`optimize <https://docs.delta.io/2.0.2/optimizations-oss.html#optimize-performance-with-file-management>`_
            operations afterwards.
        name: A unique name for the connector. If provided, this name will be used in
            logs and monitoring dashboards.
        sort_by: If specified, the output will be sorted in ascending order based on the
            values of the given columns within each minibatch. When multiple columns are provided,
            the corresponding value tuples will be compared lexicographically.
        output_table_type: Defines how the output table manages its data. If set to ``"stream_of_changes"``
            (the default), the system outputs a stream of modifications to the target table.
            This stream includes two additional integer columns: ``time``, representing the computation
            minibatch, and ``diff``, indicating the type of change (``1`` for row addition and
            ``-1`` for row deletion). If set to ``"snapshot"``, the table maintains the current
            state of the data, updated atomically with each minibatch and ensuring that no partial
            minibatch updates are visible. To correctly track the relationship between the Pathway's
            primary key and the output table in this mode, an additional ``_id`` field of the
            ``Pointer`` type is added. **Please note that this mode may be slower when there are many deletions,
            because a deletion in a minibatch causes the entire table to be rewritten once that minibatch reaches
            the output. Please also note that this method is not suitable for the tables that don't
            fit in memory.**
        table_optimizer: The optimization parameters for the output table.

    Returns:
        None

    Example:

    Consider a table ``access_log`` that needs to be output to a Delta Lake storage
    located locally at the folder ``./logs/access-log``. It can be done as follows:

    >>> pw.io.deltalake.write(access_log, "./logs/access-log")  # doctest: +SKIP

    Please note that if there is no filesystem object at this path, the corresponding
    folder will be created. However, if you run this code twice, the new data will be
    appended to the storage created during the first run.

    It is also possible to save the table to S3 storage. To save the table to the
    ``access-log`` path within the ``logs`` bucket in the ``eu-west-3`` region,
    modify the code as follows:

    >>> pw.io.deltalake.write(  # doctest: +SKIP
    ...     access_log,
    ...     "s3://logs/access-log/",
    ...     s3_connection_settings=pw.io.s3.AwsS3Settings(
    ...         bucket_name="logs",
    ...         region="eu-west-3",
    ...         access_key=os.environ["S3_ACCESS_KEY"],
    ...         secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    ...     )
    ... )

    Note that it is not necessary to specify the credentials explicitly if you are
    logged into S3. Pathway can deduce them for you. For an authorized user, the code
    can be simplified as follows:

    >>> pw.io.deltalake.write(access_log, "s3://logs/access-log/")  # doctest: +SKIP
    """
    _check_entitlements("deltalake")
    prepared_connection_settings = _prepare_s3_connection_settings(
        s3_connection_settings
    )

    prepared_partition_columns = []
    if partition_columns is not None:
        for column in partition_columns:
            if column._table != table:
                raise ValueError(
                    f"The suggested partition column {column} doesn't belong to the table {table}"
                )
            prepared_partition_columns.append(column._name)

    uri = fspath(uri)
    data_storage = api.DataStorage(
        storage_type="deltalake",
        path=uri,
        aws_s3_settings=_engine_s3_connection_settings(
            uri, prepared_connection_settings
        ),
        min_commit_frequency=min_commit_frequency,
        partition_columns=prepared_partition_columns,
        snapshot_maintenance_on_output=output_table_type == SNAPSHOT_OUTPUT_TABLE_TYPE,
        delta_optimizer_rule=(table_optimizer.engine_rule if table_optimizer else None),
    )
    data_format = api.DataFormat(
        format_type="identity",
        key_field_names=None,
        value_fields=_format_output_value_fields(table),
    )

    if table_optimizer is not None:
        if table_optimizer.tracked_column.name not in prepared_partition_columns:
            raise ValueError(
                f"Optimization is based on the column '{table_optimizer.tracked_column}', "
                "which is not a partition column. Please include this column in partition_columns."
            )
        table_optimizer._start_compression(table_path=uri)

    table.to(
        datasink.GenericDataSink(
            data_storage,
            data_format,
            datasink_name="deltalake",
            unique_name=name,
            sort_by=sort_by,
            on_pipeline_finished=(
                table_optimizer._stop_compression
                if table_optimizer is not None
                else None
            ),
        )
    )