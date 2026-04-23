def test_rabbitmq_metadata(rabbitmq_context, tmp_path: pathlib.Path):
    """Test with_metadata=True produces _metadata column with all expected fields."""
    output_file = tmp_path / "output.txt"

    # Phase 1: write messages with headers so application_properties are set
    G.clear()
    table = pw.debug.table_from_markdown(
        """
        name   | age
        Alice  | 30
        Bob    | 25
        """
    )
    pw.io.rabbitmq.write(
        table,
        uri=RABBITMQ_STREAM_URI,
        stream_name=rabbitmq_context.stream_name,
        format="json",
        headers=[table.age],
    )
    pw.run()

    # Phase 2: read back with metadata
    G.clear()

    class InputSchema(pw.Schema):
        name: str
        age: int

    table = pw.io.rabbitmq.read(
        uri=RABBITMQ_STREAM_URI,
        stream_name=rabbitmq_context.stream_name,
        schema=InputSchema,
        format="json",
        with_metadata=True,
    )
    pw.io.csv.write(table, output_file)

    wait_result_with_checker(
        CsvLinesNumberChecker(output_file, 2),
        WAIT_TIMEOUT_SECS,
    )

    result = pd.read_csv(output_file)
    assert "_metadata" in result.columns, "Expected _metadata column"
    for _, row in result.iterrows():
        metadata = json.loads(row["_metadata"])
        # Core fields always present
        assert "offset" in metadata
        assert "stream_name" in metadata
        assert metadata["stream_name"] == rabbitmq_context.stream_name
        # AMQP 1.0 property fields exist (may be null)
        for field in [
            "message_id",
            "correlation_id",
            "content_type",
            "content_encoding",
            "subject",
            "reply_to",
            "priority",
            "durable",
        ]:
            assert field in metadata, f"Expected '{field}' in metadata"
        # Application properties contain pathway_time, pathway_diff, and user header
        assert "application_properties" in metadata
        app_props = metadata["application_properties"]
        assert "pathway_time" in app_props
        assert "pathway_diff" in app_props
        assert app_props["pathway_diff"] in ("1", "-1")
        assert "age" in app_props