def test_null_header(tmp_path, kafka_context):
    output_path = tmp_path / "output.jsonl"
    kafka_context.fill(
        [
            json.dumps({"k": 0, "hdr": "foo"}),
            json.dumps(
                {"k": 1, "hdr": None}
            ),  # We output this as a header having no value
            json.dumps({"k": 2, "hdr": "bar"}),
        ]
    )

    class InputSchema(pw.Schema):
        k: int = pw.column_definition(primary_key=True)
        hdr: str | None

    table = pw.io.kafka.read(
        rdkafka_settings=kafka_context.default_rdkafka_settings(),
        topic=kafka_context.input_topic,
        format="json",
        mode="static",
        schema=InputSchema,
    )
    pw.io.kafka.write(
        table,
        rdkafka_settings=kafka_context.default_rdkafka_settings(),
        topic_name=kafka_context.output_topic,
        format="json",
        headers=[pw.this.hdr],
    )
    pw.run()
    G.clear()

    table = pw.io.kafka.read(
        rdkafka_settings=kafka_context.default_rdkafka_settings(),
        topic=kafka_context.output_topic,
        format="json",
        mode="static",
        schema=InputSchema,
        with_metadata=True,
    )
    pw.io.jsonlines.write(table, output_path)
    pw.run()

    n_rows = 0
    with open(output_path, "r") as f:
        for row in f:
            data = json.loads(row)
            key = data["k"]
            metadata = data["_metadata"]
            headers = [
                h for h in metadata["headers"] if not h[0].startswith("pathway_")
            ]
            assert len(headers) == 1
            header_key, header_value = headers[0]
            header_value = (
                base64.b64decode(header_value) if header_value is not None else None
            )
            assert header_key == "hdr"
            if key == 0:
                assert header_value == b"foo"
            elif key == 1:
                assert header_value is None
            elif key == 2:
                assert header_value == b"bar"
            else:
                raise ValueError(f"unknown key: {key}")
            n_rows += 1

    assert n_rows == 3