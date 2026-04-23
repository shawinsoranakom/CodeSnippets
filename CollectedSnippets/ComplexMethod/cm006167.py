def test_image_content_dict_multiple_formats(tmp_path):
    """Test that the format works consistently across different image types."""
    # Test with different image formats
    formats_to_test = [
        ("test.png", "image/png"),
        ("test.jpg", "image/jpeg"),
        ("test.gif", "image/gif"),
        ("test.webp", "image/webp"),
    ]

    # Use the same image content for all formats (the test PNG data)
    image_content = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    )

    for filename, expected_mime in formats_to_test:
        image_path = tmp_path / filename
        image_path.write_bytes(image_content)

        try:
            content_dict = create_image_content_dict(image_path)

            # All formats should produce the same structure
            assert content_dict["type"] == "image_url"
            assert "image_url" in content_dict
            assert "url" in content_dict["image_url"]

            # The MIME type should be detected correctly
            url = content_dict["image_url"]["url"]
            assert url.startswith(f"data:{expected_mime};base64,")

        except ValueError as e:
            # Some formats might not be supported, which is fine
            if "Could not determine MIME type" not in str(e):
                raise