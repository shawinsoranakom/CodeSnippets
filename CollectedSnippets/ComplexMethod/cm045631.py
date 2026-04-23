def run_replacement_test(
    streaming_target,
    input_format,
    expected_output_lines,
    tmp_path,
    monkeypatch,
    inputs_path_override=None,
    has_only_file_replacements=False,
):
    monkeypatch.setenv("PATHWAY_PERSISTENT_STORAGE", str(tmp_path / "PStorage"))
    inputs_path = inputs_path_override or (tmp_path / "inputs")
    os.mkdir(tmp_path / "inputs")

    class InputSchema(pw.Schema):
        key: int = pw.column_definition(primary_key=True)
        value: str

    table = pw.io.fs.read(
        inputs_path,
        format=input_format,
        schema=InputSchema,
        mode="streaming",
        autocommit_duration_ms=1,
        with_metadata=True,
    )

    output_path = tmp_path / "output.jsonl"
    pw.io.jsonlines.write(table, str(output_path))

    inputs_thread = threading.Thread(target=streaming_target, daemon=True)
    inputs_thread.start()

    wait_result_with_checker(
        FileLinesNumberChecker(output_path, expected_output_lines), 30
    )

    parsed_rows = []
    with open(output_path) as f:
        for row in f:
            parsed_row = json.loads(row)
            parsed_rows.append(parsed_row)
    parsed_rows.sort(key=lambda row: (row["time"], row["diff"]))

    key_metadata = {}
    time_removed = {}
    for parsed_row in parsed_rows:
        key = parsed_row["key"]
        metadata = parsed_row["_metadata"]
        file_name = metadata["path"]
        is_insertion = parsed_row["diff"] == 1
        timestamp = parsed_row["time"]

        if is_insertion:
            if has_only_file_replacements and file_name in time_removed:
                # If there are only replacement and the file has been removed
                # already, then we need to check that the insertion and its'
                # removal were consolidated, i.e. happened in the same timestamp
                assert time_removed[file_name] == timestamp
            key_metadata[key] = metadata
        else:
            # Check that the metadata for the deleted object corresponds to the
            # initially reported metadata
            assert key_metadata[key] == metadata
            time_removed[file_name] = timestamp