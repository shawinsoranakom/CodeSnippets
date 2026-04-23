def test_mssql_read_write_roundtrip(mssql, tmp_path):
    """Test reading from MSSQL, transforming, and writing back."""
    input_table = mssql.random_table_name()
    output_table = mssql.random_table_name()

    mssql.execute_sql(
        f"CREATE TABLE {input_table} ("
        f"  name NVARCHAR(100) NOT NULL PRIMARY KEY,"
        f"  value FLOAT NOT NULL,"
        f"  score TINYINT NOT NULL"
        f")"
    )
    mssql.insert_row(input_table, {"name": "x", "value": 10.0, "score": 1})
    mssql.insert_row(input_table, {"name": "y", "value": 20.0, "score": 2})
    mssql.insert_row(input_table, {"name": "z", "value": 30.0, "score": 255})

    class InputSchema(pw.Schema):
        name: str = pw.column_definition(primary_key=True)
        value: float
        score: int

    table = pw.io.mssql.read(
        connection_string=MSSQL_CONNECTION_STRING,
        table_name=input_table,
        schema=InputSchema,
        mode="static",
        autocommit_duration_ms=100,
    )

    # Double the values
    transformed = table.select(
        name=pw.this.name, value=pw.this.value * 2, score=pw.this.score
    )

    pw.io.mssql.write(
        transformed,
        connection_string=MSSQL_CONNECTION_STRING,
        table_name=output_table,
        init_mode="create_if_not_exists",
    )

    def run_pw():
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)

    t = threading.Thread(target=run_pw, daemon=True)
    t.start()

    # Wait for output table to be populated
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            contents = mssql.get_table_contents(
                output_table, ["name", "value", "score"]
            )
            if len(contents) >= 3:
                break
        except Exception:
            pass
        time.sleep(0.5)

    contents = mssql.get_table_contents(output_table, ["name", "value", "score"])
    contents.sort(key=lambda item: item["name"])
    assert len(contents) == 3
    assert contents[0]["name"] == "x"
    assert contents[0]["value"] == 20.0
    assert contents[0]["score"] == 1
    assert contents[1]["name"] == "y"
    assert contents[1]["value"] == 40.0
    assert contents[1]["score"] == 2
    assert contents[2]["name"] == "z"
    assert contents[2]["value"] == 60.0
    assert contents[2]["score"] == 255