def test_create_image_content_dict_format_compatibility(sample_image):
    """Test that the image content dict format is compatible with different LLM providers."""
    content_dict = create_image_content_dict(sample_image)

    # Test the new format structure that should work with Google/Gemini
    assert content_dict["type"] == "image_url"
    assert "image_url" in content_dict
    assert isinstance(content_dict["image_url"], dict)
    assert "url" in content_dict["image_url"]

    # Test that the URL is a valid data URL
    url = content_dict["image_url"]["url"]
    assert url.startswith("data:")
    assert ";base64," in url

    # Verify the structure matches OpenAI's expected format
    # OpenAI expects: {"type": "image_url", "image_url": {"url": "data:..."}}
    assert all(key in ["type", "image_url"] for key in content_dict)
    assert all(key in ["url"] for key in content_dict["image_url"])