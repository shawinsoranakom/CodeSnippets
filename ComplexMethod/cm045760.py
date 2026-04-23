def test_mssql_write_null_non_string_columns(mssql):
    """Check that NULL values round-trip correctly for every non-string optional
    column type. The write path currently binds all NULLs as Option::<String>::None
    (a typed NVARCHAR NULL in TDS); this test exposes whether SQL Server accepts
    that for BIGINT, FLOAT, BIT, and VARBINARY columns."""
    table_name = mssql.random_table_name()

    class NullableSchema(pw.Schema):
        row_id: int = pw.column_definition(primary_key=True)
        int_val: int | None
        float_val: float | None
        bool_val: bool | None
        bytes_val: bytes | None

    table = pw.debug.table_from_rows(
        NullableSchema,
        [
            (1, 42, 3.14, True, b"\x01\x02"),  # all fields populated
            (2, None, None, None, None),  # all optional fields null
        ],
    )
    pw.io.mssql.write(
        table,
        MSSQL_CONNECTION_STRING,
        table_name=table_name,
        init_mode="create_if_not_exists",
    )
    pw.run()

    mssql.execute_sql(
        f"SELECT [row_id],[int_val],[float_val],[bool_val],[bytes_val] "
        f"FROM [{table_name}] ORDER BY [row_id]"
    )
    db_rows = list(mssql.cursor.fetchall())
    assert len(db_rows) == 2

    r1_id, r1_int, r1_float, r1_bool, r1_bytes = db_rows[0]
    assert r1_id == 1
    assert r1_int == 42
    assert abs(r1_float - 3.14) < 1e-6
    assert r1_bool
    assert r1_bytes == b"\x01\x02"

    r2_id, r2_int, r2_float, r2_bool, r2_bytes = db_rows[1]
    assert r2_id == 2
    assert r2_int is None
    assert r2_float is None
    assert r2_bool is None
    assert r2_bytes is None