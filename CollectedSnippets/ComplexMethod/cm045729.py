def test_iceberg_streaming(backend, tmp_path, s3_path):
    inputs_path = tmp_path / "inputs"
    output_path = tmp_path / "output.jsonl"
    full_s3_path = f"s3://aws-integrationtest/{s3_path}"
    inputs_path.mkdir()
    table_name = uuid.uuid4().hex
    namespace = uuid.uuid4().hex

    def stream_inputs():
        for i in range(1, len(INPUT_CONTENTS) + 1):
            input_path = inputs_path / f"{i}.txt"
            input_path.write_text(INPUT_CONTENTS[i])
            wait_result_with_checker(
                FileLinesNumberChecker(output_path, 4 * i),
                30,
                target=None,
            )

    class InputSchema(pw.Schema):
        user_id: int
        name: str

    table = pw.io.jsonlines.read(
        inputs_path,
        schema=InputSchema,
        mode="streaming",
    )
    # It's much quicker to check the file to make sure entries are ingested,
    # rather than to query the catalog
    pw.io.jsonlines.write(table, output_path)
    pw.io.iceberg.write(
        table,
        catalog=_get_catalog(backend, s3_path=full_s3_path),
        namespace=[namespace],
        table_name=table_name,
        min_commit_frequency=1000,
    )

    t = threading.Thread(target=stream_inputs)
    t.start()
    wait_result_with_checker(
        IcebergEntriesCountChecker(
            backend, f"{namespace}.{table_name}", 4 * len(INPUT_CONTENTS)
        ),
        timeout_sec=100,
    )

    all_ids = set()
    all_names = set()
    for i in range(1, len(INPUT_CONTENTS) + 1):
        for input_line in INPUT_CONTENTS[i].splitlines():
            data = json.loads(input_line)
            all_ids.add(data["user_id"])
            all_names.add(data["name"])

    pandas_table = _get_pandas_table(backend, f"{namespace}.{table_name}")
    assert pandas_table.shape == (4 * len(INPUT_CONTENTS), 4)
    assert set(pandas_table["user_id"]) == all_ids
    assert set(pandas_table["name"]) == all_names
    assert set(pandas_table["diff"]) == {1}
    assert len(set(pandas_table["time"])) == len(INPUT_CONTENTS)