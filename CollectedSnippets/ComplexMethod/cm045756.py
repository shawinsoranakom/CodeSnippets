def test_mssql_read_basic(mssql, tmp_path):
    """Test basic read from an MSSQL table."""
    table_name = mssql.random_table_name()
    mssql.execute_sql(
        f"CREATE TABLE {table_name} ("
        f"  sensor_name NVARCHAR(100) NOT NULL PRIMARY KEY,"
        f"  temperature FLOAT NOT NULL,"
        f"  humidity FLOAT NOT NULL"
        f")"
    )
    mssql.insert_row(
        table_name, {"sensor_name": "A", "temperature": 22.5, "humidity": 45.0}
    )
    mssql.insert_row(
        table_name, {"sensor_name": "B", "temperature": 23.1, "humidity": 42.3}
    )
    mssql.insert_row(
        table_name, {"sensor_name": "C", "temperature": 21.0, "humidity": 50.2}
    )

    class SensorSchema(pw.Schema):
        sensor_name: str = pw.column_definition(primary_key=True)
        temperature: float
        humidity: float

    output_path = tmp_path / "output.jsonl"

    table = pw.io.mssql.read(
        connection_string=MSSQL_CONNECTION_STRING,
        table_name=table_name,
        schema=SensorSchema,
        mode="static",
        autocommit_duration_ms=100,
    )
    pw.io.jsonlines.write(table, str(output_path))

    def run_pw():
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)

    t = threading.Thread(target=run_pw, daemon=True)
    t.start()

    # Wait for output to appear
    deadline = time.time() + 30
    while time.time() < deadline:
        if output_path.exists():
            lines = output_path.read_text().strip().split("\n")
            if len(lines) >= 3:
                break
        time.sleep(0.5)

    assert output_path.exists()
    lines = output_path.read_text().strip().split("\n")
    assert len(lines) >= 3

    records = [json.loads(line) for line in lines]
    sensor_names = sorted([r["sensor_name"] for r in records])
    assert sensor_names == ["A", "B", "C"]