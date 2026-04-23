def test_name_pattern_single_filter(
    list_objects_strategy,
    format,
    with_metadata,
    name_pattern,
    tmp_path,
    credentials_dir,
):
    object_size_limit = None

    NUM_TXT_FILES = 2
    NUM_CSV_FILES = 1
    NUM_MD_FILES = 1
    NUM_PDF_FILES = 0

    files_table = pw.io.gdrive.read(
        FOLDER_WITH_TYPES,
        mode="static",
        format=format,
        service_user_credentials_file=credentials_dir / "credentials.json",
        object_size_limit=object_size_limit,
        with_metadata=with_metadata,
        file_name_pattern=name_pattern,
        _list_objects_strategy=list_objects_strategy,
    )

    pw.io.jsonlines.write(files_table, tmp_path / "output.jsonl")
    pw.run()

    rows_count = 0
    with open(tmp_path / "output.jsonl", "r") as f:
        for raw_row in f:
            row = json.loads(raw_row)
            if format == "binary":
                assert "data" in row
            elif format == "only_metadata":
                assert "data" not in row
            else:
                raise ValueError(f"unknown format: {format}")

            if with_metadata or format == "only_metadata":
                metadata = row["_metadata"]
                assert metadata["status"] == pw.io.gdrive.STATUS_DOWNLOADED
            rows_count += 1

    if name_pattern == "*.txt":
        assert rows_count == NUM_TXT_FILES
    elif name_pattern == "*.csv":
        assert rows_count == NUM_CSV_FILES
    elif name_pattern == ["*.txt", "*.csv"]:
        assert rows_count == NUM_TXT_FILES + NUM_CSV_FILES
    elif name_pattern == "*.md":
        assert rows_count == NUM_MD_FILES
    elif name_pattern == "*.pdf":
        assert rows_count == NUM_PDF_FILES
    elif name_pattern == ["*.txt", "*.pdf", "*.xlsx", "non_existent.txt"]:
        assert rows_count == NUM_TXT_FILES + NUM_PDF_FILES
    elif name_pattern == ["first.txt", "random.csv"]:
        assert rows_count == 2
    elif name_pattern is None:
        assert (
            rows_count == NUM_TXT_FILES + NUM_CSV_FILES + NUM_MD_FILES + NUM_PDF_FILES
        )