def sql_flush(style, connection, reset_sequences=True, allow_cascade=False):
    """
    Return a list of the SQL statements used to flush the database.
    """
    tables = connection.introspection.django_table_names(
        only_existing=True, include_views=False
    )
    return connection.ops.sql_flush(
        style,
        tables,
        reset_sequences=reset_sequences,
        allow_cascade=allow_cascade,
    )