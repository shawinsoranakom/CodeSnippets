def test_kinesis_output_simple(format, specify_key, kinesis_context):
    table = pw.debug.table_from_markdown(
        """
        | key | value
     1  |   1 | one
     2  |   2 | two
     3  |   3 | three
    """
    )

    extra_kwargs = {}
    if specify_key:
        extra_kwargs["partition_key"] = table.key
    if format != "json":
        extra_kwargs["data"] = table.value

    pw.io.kinesis.write(
        table,
        stream_name=kinesis_context.stream_name,
        format=format,
        **extra_kwargs,
    )
    pw.run()
    shards = kinesis_context.list_shards_and_statuses()
    assert len(shards) == 1

    expected_entry = {
        1: "one",
        2: "two",
        3: "three",
    }
    user_defined_values = expected_entry.values()

    records = kinesis_context.read_shard_records(shards[0].shard_id)
    for record in records:
        key_is_user_defined = record.key in {"1", "2", "3"}
        assert key_is_user_defined == specify_key
        if format == "json":
            data = json.loads(record.value.decode("utf-8"))
            assert expected_entry[data["key"]] == data["value"]
        elif format == "plaintext":
            assert record.value.decode("utf-8") in user_defined_values
        elif format == "raw":
            assert record.value.decode("utf-8") in user_defined_values