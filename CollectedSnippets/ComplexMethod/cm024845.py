async def test_get_url_external(hass: HomeAssistant) -> None:
    """Test getting an instance URL when the user has set an external URL."""
    assert hass.config.external_url is None

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_current_request=True)

    # Test with external URL: http://example.com:8123
    await async_process_ha_core_config(
        hass,
        {"external_url": "http://example.com:8123"},
    )

    assert hass.config.external_url == "http://example.com:8123"
    assert _get_external_url(hass) == "http://example.com:8123"
    assert _get_external_url(hass, allow_cloud=False) == "http://example.com:8123"
    assert _get_external_url(hass, allow_ip=False) == "http://example.com:8123"
    assert _get_external_url(hass, prefer_cloud=True) == "http://example.com:8123"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_current_request=True)

    with patch(
        "homeassistant.helpers.network._get_request_host", return_value="example.com"
    ):
        assert (
            _get_external_url(hass, require_current_request=True)
            == "http://example.com:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(
                hass, require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(hass, require_current_request=True, require_ssl=True)

    with (
        patch(
            "homeassistant.helpers.network._get_request_host",
            return_value="no_match.example.com",
        ),
        pytest.raises(NoURLAvailableError),
    ):
        _get_external_url(hass, require_current_request=True)

    # Test with external URL: http://example.com:80/
    await async_process_ha_core_config(
        hass,
        {"external_url": "http://example.com:80/"},
    )

    assert hass.config.external_url == "http://example.com:80/"
    assert _get_external_url(hass) == "http://example.com"
    assert _get_external_url(hass, allow_cloud=False) == "http://example.com"
    assert _get_external_url(hass, allow_ip=False) == "http://example.com"
    assert _get_external_url(hass, prefer_cloud=True) == "http://example.com"
    assert _get_external_url(hass, require_standard_port=True) == "http://example.com"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_ssl=True)

    # Test with external url: https://example.com:443/
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com:443/"},
    )
    assert hass.config.external_url == "https://example.com:443/"
    assert _get_external_url(hass) == "https://example.com"
    assert _get_external_url(hass, allow_cloud=False) == "https://example.com"
    assert _get_external_url(hass, allow_ip=False) == "https://example.com"
    assert _get_external_url(hass, prefer_cloud=True) == "https://example.com"
    assert _get_external_url(hass, require_ssl=False) == "https://example.com"
    assert _get_external_url(hass, require_standard_port=True) == "https://example.com"

    # Test with external URL: https://example.com:80
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com:80"},
    )
    assert hass.config.external_url == "https://example.com:80"
    assert _get_external_url(hass) == "https://example.com:80"
    assert _get_external_url(hass, allow_cloud=False) == "https://example.com:80"
    assert _get_external_url(hass, allow_ip=False) == "https://example.com:80"
    assert _get_external_url(hass, prefer_cloud=True) == "https://example.com:80"
    assert _get_external_url(hass, require_ssl=True) == "https://example.com:80"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_standard_port=True)

    # Test with external URL: https://192.168.0.1
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://192.168.0.1"},
    )
    assert hass.config.external_url == "https://192.168.0.1"
    assert _get_external_url(hass) == "https://192.168.0.1"
    assert _get_external_url(hass, allow_cloud=False) == "https://192.168.0.1"
    assert _get_external_url(hass, prefer_cloud=True) == "https://192.168.0.1"
    assert _get_external_url(hass, require_standard_port=True) == "https://192.168.0.1"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_ssl=True)

    with patch(
        "homeassistant.helpers.network._get_request_host", return_value="192.168.0.1"
    ):
        assert (
            _get_external_url(hass, require_current_request=True)
            == "https://192.168.0.1"
        )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(hass, require_current_request=True, allow_ip=False)

        with pytest.raises(NoURLAvailableError):
            _get_external_url(hass, require_current_request=True, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(hass, require_cloud=True)

    with patch(
        "homeassistant.components.cloud.async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        hass.config.components.add("cloud")
        assert (
            _get_external_url(hass, require_cloud=True) == "https://example.nabu.casa"
        )