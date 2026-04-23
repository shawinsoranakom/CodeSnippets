def test_mssql_cdc_read_updates(mssql, tmp_path):
    """Test CDC reader detects updates (emits delete + insert)."""
    table_name = mssql.random_table_name()
    mssql.execute_sql(
        f"CREATE TABLE {table_name} ("
        f"  id INT PRIMARY KEY,"
        f"  value NVARCHAR(100) NOT NULL"
        f")"
    )
    mssql.enable_cdc(table_name)

    mssql.insert_row(table_name, {"id": 1, "value": "original"})

    class TestSchema(pw.Schema):
        id: int = pw.column_definition(primary_key=True)
        value: str

    output_path = tmp_path / "cdc_update_output.jsonl"

    table = pw.io.mssql.read(
        connection_string=MSSQL_CONNECTION_STRING,
        table_name=table_name,
        schema=TestSchema,
        mode="streaming",
        autocommit_duration_ms=100,
    )
    pw.io.jsonlines.write(table, str(output_path))

    def run_pw():
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)

    t = threading.Thread(target=run_pw, daemon=True)
    t.start()

    # Wait for initial snapshot
    deadline = time.time() + 30
    while time.time() < deadline:
        if output_path.exists():
            lines = output_path.read_text().strip().split("\n")
            if len(lines) >= 1:
                break
        time.sleep(0.5)

    # Update the row — CDC should emit delete (old) + insert (new)
    mssql.execute_sql(f"UPDATE {table_name} SET value = 'updated' WHERE id = 1")

    # Wait for the update events
    deadline = time.time() + 30
    while time.time() < deadline:
        lines = output_path.read_text().strip().split("\n")
        if len(lines) >= 2:
            break
        time.sleep(0.5)

    lines = output_path.read_text().strip().split("\n")
    records = [json.loads(line) for line in lines]
    values = [r["value"] for r in records]
    assert "updated" in values