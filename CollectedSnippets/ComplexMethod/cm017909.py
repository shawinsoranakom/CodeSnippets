def test_data_uris() -> None:
    # Test basic parsing of data URIs
    data_uri = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type is None
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain;charset=utf-8;base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 1
    assert attributes["charset"] == "utf-8"
    assert data == b"Hello, World!"

    data_uri = "data:,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type is None
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain;charset=utf-8,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 1
    assert attributes["charset"] == "utf-8"
    assert data == b"Hello, World!"