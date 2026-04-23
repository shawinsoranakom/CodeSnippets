def test_file_uris() -> None:
    # Test file URI with an empty host
    file_uri = "file:///path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with no host
    file_uri = "file:/path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with localhost
    file_uri = "file://localhost/path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc == "localhost"
    assert path == "/path/to/file.txt"

    # Test file URI with query parameters
    file_uri = "file:///path/to/file.txt?param=value"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with fragment
    file_uri = "file:///path/to/file.txt#fragment"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"