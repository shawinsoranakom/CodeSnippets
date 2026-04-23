def test_derive_folder_and_filename_from_url():
    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/file.tar.gz"
    )
    assert folder == "example.com"
    assert filename == "file.tar.gz"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/نمونه نماینده.data"
    )
    assert folder == "example.com"
    assert filename == "نمونه-نماینده.data"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/path/to-/.file.tar.gz"
    )
    assert folder == "example.com/path_to"
    assert filename == "file.tar.gz"

    folder, filename = _derive_folder_and_filename_from_url("https://example.com/")
    assert folder == "example.com"
    assert filename == "downloaded_file"

    folder, filename = _derive_folder_and_filename_from_url("https://example.com")
    assert folder == "example.com"
    assert filename == "downloaded_file"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/path/@to/data.json?param=value"
    )
    assert folder == "example.com/path_to"
    assert filename == "data.json"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/path/@@to._/-_.data.json.#anchor"
    )
    assert folder == "example.com/path_to"
    assert filename == "data.json"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com//some_file.txt"
    )
    assert folder == "example.com"
    assert filename == "some_file.txt"

    folder, filename = _derive_folder_and_filename_from_url(
        "http://example/../some_file.txt"
    )
    assert folder == "example"
    assert filename == "some_file.txt"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/!.'.,/some_file.txt"
    )
    assert folder == "example.com"
    assert filename == "some_file.txt"

    folder, filename = _derive_folder_and_filename_from_url(
        "https://example.com/a/!.'.,/b/some_file.txt"
    )
    assert folder == "example.com/a_b"
    assert filename == "some_file.txt"

    folder, filename = _derive_folder_and_filename_from_url("https://example.com/!.'.,")
    assert folder == "example.com"
    assert filename == "downloaded_file"

    with pytest.raises(ValueError, match="Invalid URL"):
        _derive_folder_and_filename_from_url("https:/../")