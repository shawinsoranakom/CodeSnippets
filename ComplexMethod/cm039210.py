def test_fetch_file_without_sha256(monkeypatch, tmpdir):
    server_side = tmpdir.mkdir("server_side")
    data_file = Path(server_side / "data.jsonl")
    server_data = '{"a": 1, "b": 2}\n'
    data_file.write_text(server_data, encoding="utf-8")

    client_side = tmpdir.mkdir("client_side")

    urlretrieve_mock = _mock_urlretrieve(server_side)
    monkeypatch.setattr("sklearn.datasets._base.urlretrieve", urlretrieve_mock)

    # The first call should trigger a download:
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl",
        folder=client_side,
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 1

    # Fetching again the same file to the same folder should do nothing:
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl",
        folder=client_side,
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 1

    # Deleting and calling again should re-download
    fetched_file_path.unlink()
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl",
        folder=client_side,
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 2