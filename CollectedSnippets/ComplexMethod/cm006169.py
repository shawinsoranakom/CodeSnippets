def test_error_handling_without_api_keys(sample_image):
    """Test that image content dict format is valid even without API access."""
    content_dict = create_image_content_dict(sample_image)

    # The format should be correct regardless of API availability
    assert content_dict["type"] == "image_url"
    assert "image_url" in content_dict
    assert "url" in content_dict["image_url"]

    # Should not contain legacy fields that caused provider issues
    assert "source_type" not in content_dict
    assert "source" not in content_dict
    assert "media_type" not in content_dict

    # URL should be a valid data URL
    url = content_dict["image_url"]["url"]
    assert url.startswith("data:image/")
    assert ";base64," in url

    # Base64 part should be valid
    base64_part = url.split(";base64,")[1]
    assert base64.b64decode(base64_part)