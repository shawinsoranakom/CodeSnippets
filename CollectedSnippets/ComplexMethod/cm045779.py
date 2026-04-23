def test_kafka_message_metadata(tmp_path, kafka_context):
    test_kafka_foo_message_headers = [
        ("X-Sender-ID", b"pathway-integration-test"),
        ("X-Trace-ID", b"a8acf0a5-009f-4035-9aca-834bc85929f9"),
        ("X-Trace-ID", b"7a21cee9-c081-4d64-add1-06e2e5e592d6"),
        ("X-Origin", b""),
        ("X-Signature", bytes([0, 255, 128, 10])),
    ]
    test_kafka_bar_message_headers = [
        ("X-Sender-ID", b"pathway-integration-test"),
        ("X-Trace-ID", b"ee6e3017-d77f-43d9-abf6-c33bd51e27ef"),
        ("X-Trace-ID", b"092565ae-aa1e-406c-a53f-d2c4d6f2397c"),
        ("X-Trace-ID", b"1d0ae9e7-8cac-40d8-9072-3d1a919a2fef"),
        ("X-Origin", b"Server"),
        ("X-Signature", bytes([0, 255, 128, 10, 17])),
    ]

    def check_headers(parsed: list[list[str]], original: list[tuple[str, bytes]]):
        decoded_headers = []
        for key, value in parsed:
            decoded_value = base64.b64decode(value)
            decoded_headers.append((key, decoded_value))
        decoded_headers.sort()
        original.sort()
        assert decoded_headers == original

    kafka_context.fill(["foo"], headers=test_kafka_foo_message_headers)
    kafka_context.fill(["bar"], headers=test_kafka_bar_message_headers)

    table = pw.io.kafka.read(
        rdkafka_settings=kafka_context.default_rdkafka_settings(),
        topic=kafka_context.input_topic,
        format="plaintext",
        autocommit_duration_ms=100,
        with_metadata=True,
    )
    output_path = tmp_path / "output.jsonl"

    pw.io.jsonlines.write(table, output_path)
    wait_result_with_checker(FileLinesNumberChecker(output_path, 2), 10)

    offsets = set()
    with open(output_path, "r") as f:
        for row in f:
            data = json.loads(row)
            metadata = data["_metadata"]
            assert metadata["topic"] == kafka_context.input_topic
            assert "partition" in metadata
            assert "offset" in metadata
            offsets.add(metadata["offset"])

            assert "headers" in metadata
            headers = metadata["headers"]
            if data["data"] == "foo":
                check_headers(headers, test_kafka_foo_message_headers)
            elif data["data"] == "bar":
                check_headers(headers, test_kafka_bar_message_headers)
            else:
                raise ValueError(f"unknown message data: {data['data']}")

    assert len(offsets) == 2