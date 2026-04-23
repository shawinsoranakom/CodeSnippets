async def test_is_hass_url(hass: HomeAssistant) -> None:
    """Test is_hass_url."""
    assert hass.config.api is None
    assert hass.config.internal_url is None
    assert hass.config.external_url is None

    assert is_hass_url(hass, "http://example.com") is False
    assert is_hass_url(hass, "bad_url") is False
    assert is_hass_url(hass, "bad_url.com") is False
    assert is_hass_url(hass, "http:/bad_url.com") is False

    hass.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")
    assert is_hass_url(hass, "http://192.168.123.123:8123") is True
    assert is_hass_url(hass, "https://192.168.123.123:8123") is False
    assert is_hass_url(hass, "http://192.168.123.123") is False

    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )
    assert is_hass_url(hass, "http://example.local:8123") is True
    assert is_hass_url(hass, "https://example.local:8123") is False
    assert is_hass_url(hass, "http://example.local") is False

    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com:443"},
    )
    assert is_hass_url(hass, "https://example.com:443") is True
    assert is_hass_url(hass, "https://example.com") is True
    assert is_hass_url(hass, "http://example.com:443") is False
    assert is_hass_url(hass, "http://example.com") is False

    with patch(
        "homeassistant.components.cloud.async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert is_hass_url(hass, "https://example.nabu.casa") is False

        hass.config.components.add("cloud")
        assert is_hass_url(hass, "https://example.nabu.casa:443") is True
        assert is_hass_url(hass, "https://example.nabu.casa") is True
        assert is_hass_url(hass, "http://example.nabu.casa:443") is False
        assert is_hass_url(hass, "http://example.nabu.casa") is False