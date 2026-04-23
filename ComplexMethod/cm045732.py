def test_formats_without_parsing(
    storage_type, format, with_metadata, tmp_path, s3_path
):
    input_path = f"{s3_path}/input.txt"
    input_full_contents = "abc\n\ndef\nghi\njkl"
    output_path = tmp_path / "output.json"
    uploaded_at = int(time.time())

    put_object_into_storage(storage_type, input_path, input_full_contents)
    table = create_table_for_storage(
        storage_type, input_path, format, with_metadata=with_metadata
    )
    pw.io.jsonlines.write(table, output_path)
    pw.run()

    def check_metadata(metadata):
        assert uploaded_at <= metadata["modified_at"] <= uploaded_at + 10
        assert metadata["path"] == input_path
        assert metadata["size"] == len(input_full_contents)

    if format in ("binary", "plaintext_by_object"):
        expected_output = (
            base64.b64encode(input_full_contents.encode("utf-8")).decode("utf-8")
            if format == "binary"
            else input_full_contents
        )
        with open(output_path) as f:
            result = json.load(f)
            assert result["data"] == expected_output
            if with_metadata:
                check_metadata(result["_metadata"])
    else:
        lines = []
        with open(output_path, "r") as f:
            for row in f:
                result = json.loads(row)
                lines.append(result["data"])
                if with_metadata:
                    check_metadata(result["_metadata"])
        lines.sort()
        target = input_full_contents.split("\n")
        target.sort()
        assert lines == target