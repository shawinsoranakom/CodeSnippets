def test_stream_info_operations() -> None:
    """Test operations performed on StreamInfo objects."""

    stream_info_original = StreamInfo(
        mimetype="mimetype.1",
        extension="extension.1",
        charset="charset.1",
        filename="filename.1",
        local_path="local_path.1",
        url="url.1",
    )

    # Check updating all attributes by keyword
    keywords = ["mimetype", "extension", "charset", "filename", "local_path", "url"]
    for keyword in keywords:
        updated_stream_info = stream_info_original.copy_and_update(
            **{keyword: f"{keyword}.2"}
        )

        # Make sure the targted attribute is updated
        assert getattr(updated_stream_info, keyword) == f"{keyword}.2"

        # Make sure the other attributes are unchanged
        for k in keywords:
            if k != keyword:
                assert getattr(stream_info_original, k) == getattr(
                    updated_stream_info, k
                )

    # Check updating all attributes by passing a new StreamInfo object
    keywords = ["mimetype", "extension", "charset", "filename", "local_path", "url"]
    for keyword in keywords:
        updated_stream_info = stream_info_original.copy_and_update(
            StreamInfo(**{keyword: f"{keyword}.2"})
        )

        # Make sure the targted attribute is updated
        assert getattr(updated_stream_info, keyword) == f"{keyword}.2"

        # Make sure the other attributes are unchanged
        for k in keywords:
            if k != keyword:
                assert getattr(stream_info_original, k) == getattr(
                    updated_stream_info, k
                )

    # Check mixing and matching
    updated_stream_info = stream_info_original.copy_and_update(
        StreamInfo(extension="extension.2", filename="filename.2"),
        mimetype="mimetype.3",
        charset="charset.3",
    )
    assert updated_stream_info.extension == "extension.2"
    assert updated_stream_info.filename == "filename.2"
    assert updated_stream_info.mimetype == "mimetype.3"
    assert updated_stream_info.charset == "charset.3"
    assert updated_stream_info.local_path == "local_path.1"
    assert updated_stream_info.url == "url.1"

    # Check multiple StreamInfo objects
    updated_stream_info = stream_info_original.copy_and_update(
        StreamInfo(extension="extension.4", filename="filename.5"),
        StreamInfo(mimetype="mimetype.6", charset="charset.7"),
    )
    assert updated_stream_info.extension == "extension.4"
    assert updated_stream_info.filename == "filename.5"
    assert updated_stream_info.mimetype == "mimetype.6"
    assert updated_stream_info.charset == "charset.7"
    assert updated_stream_info.local_path == "local_path.1"
    assert updated_stream_info.url == "url.1"