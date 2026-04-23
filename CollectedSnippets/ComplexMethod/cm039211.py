def test_fetch_file_with_sha256(monkeypatch, tmpdir):
    server_side = tmpdir.mkdir("server_side")
    data_file = Path(server_side / "data.jsonl")
    server_data = '{"a": 1, "b": 2}\n'
    data_file.write_text(server_data, encoding="utf-8")
    expected_sha256 = hashlib.sha256(data_file.read_bytes()).hexdigest()

    client_side = tmpdir.mkdir("client_side")

    urlretrieve_mock = _mock_urlretrieve(server_side)
    monkeypatch.setattr("sklearn.datasets._base.urlretrieve", urlretrieve_mock)

    # The first call should trigger a download.
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl", folder=client_side, sha256=expected_sha256
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 1

    # Fetching again the same file to the same folder should do nothing when
    # the sha256 match:
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl", folder=client_side, sha256=expected_sha256
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 1

    # Corrupting the local data should yield a warning and trigger a new download:
    fetched_file_path.write_text("corrupted contents", encoding="utf-8")
    expected_msg = (
        r"SHA256 checksum of existing local file data.jsonl "
        rf"\(.*\) differs from expected \({expected_sha256}\): "
        r"re-downloading from https://example.com/data.jsonl \."
    )
    with pytest.warns(match=expected_msg):
        fetched_file_path = fetch_file(
            "https://example.com/data.jsonl", folder=client_side, sha256=expected_sha256
        )
        assert fetched_file_path == client_side / "data.jsonl"
        assert fetched_file_path.read_text(encoding="utf-8") == server_data
        assert urlretrieve_mock.call_count == 2

    # Calling again should do nothing:
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl", folder=client_side, sha256=expected_sha256
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 2

    # Deleting the local file and calling again should redownload without warning:
    fetched_file_path.unlink()
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl", folder=client_side, sha256=expected_sha256
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 3

    # Calling without a sha256 should also work without redownloading:
    fetched_file_path = fetch_file(
        "https://example.com/data.jsonl",
        folder=client_side,
    )
    assert fetched_file_path == client_side / "data.jsonl"
    assert fetched_file_path.read_text(encoding="utf-8") == server_data
    assert urlretrieve_mock.call_count == 3

    # Calling with a wrong sha256 should raise an informative exception:
    non_matching_sha256 = "deadbabecafebeef"
    expected_warning_msg = "differs from expected"
    expected_error_msg = re.escape(
        f"The SHA256 checksum of data.jsonl ({expected_sha256}) differs from "
        f"expected ({non_matching_sha256})."
    )
    with pytest.raises(OSError, match=expected_error_msg):
        with pytest.warns(match=expected_warning_msg):
            fetch_file(
                "https://example.com/data.jsonl",
                folder=client_side,
                sha256=non_matching_sha256,
            )