async def test_get_external_url_cloud_fallback(hass: HomeAssistant) -> None:
    """Test getting an external instance URL with cloud fallback."""
    assert hass.config.external_url is None

    # Test with external URL: http://1.1.1.1:8123
    await async_process_ha_core_config(
        hass,
        {"external_url": "http://1.1.1.1:8123"},
    )

    assert hass.config.external_url == "http://1.1.1.1:8123"
    assert _get_external_url(hass, prefer_cloud=True) == "http://1.1.1.1:8123"

    # Add Cloud to the previous test
    hass.config.components.add("cloud")
    with patch(
        "homeassistant.components.cloud.async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert _get_external_url(hass, allow_cloud=False) == "http://1.1.1.1:8123"
        assert _get_external_url(hass, allow_ip=False) == "https://example.nabu.casa"
        assert _get_external_url(hass, prefer_cloud=False) == "http://1.1.1.1:8123"
        assert _get_external_url(hass, prefer_cloud=True) == "https://example.nabu.casa"
        assert _get_external_url(hass, require_ssl=True) == "https://example.nabu.casa"
        assert (
            _get_external_url(hass, require_standard_port=True)
            == "https://example.nabu.casa"
        )

    # Test with external URL: https://example.com
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )

    assert hass.config.external_url == "https://example.com"
    assert _get_external_url(hass, prefer_cloud=True) == "https://example.com"

    # Add Cloud to the previous test
    hass.config.components.add("cloud")
    with patch(
        "homeassistant.components.cloud.async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert _get_external_url(hass, allow_cloud=False) == "https://example.com"
        assert _get_external_url(hass, allow_ip=False) == "https://example.com"
        assert _get_external_url(hass, prefer_cloud=False) == "https://example.com"
        assert _get_external_url(hass, prefer_cloud=True) == "https://example.nabu.casa"
        assert _get_external_url(hass, require_ssl=True) == "https://example.com"
        assert (
            _get_external_url(hass, require_standard_port=True) == "https://example.com"
        )
        assert (
            _get_external_url(hass, prefer_cloud=True, allow_cloud=False)
            == "https://example.com"
        )