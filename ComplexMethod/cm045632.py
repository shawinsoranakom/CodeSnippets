def test_pyfilesystem_simple(tmp_path: pathlib.Path):
    zip_path = (
        pathlib.Path("/".join(__file__.split("/")[:-1])) / "data" / "pyfs-testdata.zip"
    )
    output_path = tmp_path / "output.txt"

    with open_fs("zip://" + str(zip_path)) as source:
        table = pw.io.pyfilesystem.read(
            source,
            mode="static",
            with_metadata=True,
        )
        pw.io.jsonlines.write(table, output_path)
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)

    paths = set()
    names = set()
    with open(output_path, "r") as f:
        for line in f:
            data = json.loads(line)
            assert "_metadata" in data
            assert "data" in data
            assert "diff" in data
            assert "time" in data
            metadata = data["_metadata"]
            paths.add(metadata["path"])
            names.add(metadata["name"])
            assert metadata["size"] == len(base64.b64decode(data["data"]))

    assert names == set(["a.txt", "b.txt"])
    assert paths == set(["projects/a.txt", "projects/b.txt"])