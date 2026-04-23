def setup_databases(
    verbosity,
    interactive,
    *,
    time_keeper=None,
    keepdb=False,
    debug_sql=False,
    parallel=0,
    aliases=None,
    serialized_aliases=None,
    **kwargs,
):
    """Create the test databases."""
    if time_keeper is None:
        time_keeper = NullTimeKeeper()

    test_databases, mirrored_aliases = get_unique_databases_and_mirrors(aliases)

    old_names = []
    serialize_connections = []

    for db_name, aliases in test_databases.values():
        first_alias = None
        for alias in aliases:
            connection = connections[alias]
            old_names.append((connection, db_name, first_alias is None))

            # Actually create the database for the first connection
            if first_alias is None:
                first_alias = alias
                with time_keeper.timed("  Creating '%s'" % alias):
                    connection.creation.create_test_db(
                        verbosity=verbosity,
                        autoclobber=not interactive,
                        keepdb=keepdb,
                    )
                    if serialized_aliases is None or alias in serialized_aliases:
                        serialize_connections.append(connection)
                if parallel > 1:
                    for index in range(parallel):
                        with time_keeper.timed("  Cloning '%s'" % alias):
                            connection.creation.clone_test_db(
                                suffix=str(index + 1),
                                verbosity=verbosity,
                                keepdb=keepdb,
                            )
            # Configure all other connections as mirrors of the first one
            else:
                connections[alias].creation.set_as_test_mirror(
                    connections[first_alias].settings_dict
                )

    # Configure the test mirrors.
    for alias, mirror_alias in mirrored_aliases.items():
        connections[alias].creation.set_as_test_mirror(
            connections[mirror_alias].settings_dict
        )

    # Serialize content of test databases only once all of them are setup to
    # account for database mirroring and routing during serialization. This
    # slightly horrific process is so people who are testing on databases
    # without transactions or using TransactionTestCase still get a clean
    # database on every test run.
    for serialize_connection in serialize_connections:
        serialize_connection._test_serialized_contents = (
            serialize_connection.creation.serialize_db_to_string()
        )

    if debug_sql:
        for alias in connections:
            connections[alias].force_debug_cursor = True

    return old_names