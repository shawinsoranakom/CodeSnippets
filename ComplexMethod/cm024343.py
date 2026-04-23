async def test_default_provider_attributes() -> None:
    """Test default provider attributes."""
    provider = DefaultProvider()

    assert provider.hass is None
    assert provider.name is None
    assert provider.default_language is None
    assert provider.supported_languages == SUPPORT_LANGUAGES
    assert provider.supported_options is None
    assert provider.default_options is None
    assert provider.async_get_supported_voices("test") is None