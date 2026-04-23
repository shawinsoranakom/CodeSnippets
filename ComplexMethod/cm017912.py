def test_markitdown_exiftool() -> None:
    which_exiftool = shutil.which("exiftool")
    assert which_exiftool is not None

    # Test explicitly setting the location of exiftool
    markitdown = MarkItDown(exiftool_path=which_exiftool)
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test.jpg"))
    for key in JPG_TEST_EXIFTOOL:
        target = f"{key}: {JPG_TEST_EXIFTOOL[key]}"
        assert target in result.text_content

    # Test setting the exiftool path through an environment variable
    os.environ["EXIFTOOL_PATH"] = which_exiftool
    markitdown = MarkItDown()
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test.jpg"))
    for key in JPG_TEST_EXIFTOOL:
        target = f"{key}: {JPG_TEST_EXIFTOOL[key]}"
        assert target in result.text_content

    # Test some other media types
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test.mp3"))
    for key in MP3_TEST_EXIFTOOL:
        target = f"{key}: {MP3_TEST_EXIFTOOL[key]}"
        assert target in result.text_content