def test_single_file_read_with_constraints(
    list_objects_strategy, object_size_limit, with_metadata, tmp_path, credentials_dir
):
    files_table = pw.io.gdrive.read(
        FOLDER_WITH_ONE_FILE_ID,
        mode="static",
        service_user_credentials_file=credentials_dir / "credentials.json",
        object_size_limit=object_size_limit,
        with_metadata=with_metadata,
        _list_objects_strategy=list_objects_strategy,
    )
    pw.io.jsonlines.write(files_table, tmp_path / "output.jsonl")
    pw.run()
    rows_count = 0
    with open(tmp_path / "output.jsonl", "r") as f:
        for raw_row in f:
            row = json.loads(raw_row)
            if object_size_limit is None or object_size_limit > TEST_FILE_SIZE:
                target_status = pw.io.gdrive.STATUS_DOWNLOADED
                decoded_data = base64.b64decode(row["data"])
                assert len(decoded_data) == TEST_FILE_SIZE
            else:
                target_status = pw.io.gdrive.STATUS_SIZE_LIMIT_EXCEEDED
                assert len(row["data"]) == 0
            if with_metadata:
                metadata = row["_metadata"]
                assert metadata["status"] == target_status
            rows_count += 1
    assert rows_count == 1