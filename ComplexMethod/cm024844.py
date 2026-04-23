async def test_get_url_internal(hass: HomeAssistant) -> None:
    """Test getting an instance URL when the user has set an internal URL."""
    assert hass.config.internal_url is None

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_current_request=True)

    # Test with internal URL: http://example.local:8123
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )

    assert hass.config.internal_url == "http://example.local:8123"
    assert _get_internal_url(hass) == "http://example.local:8123"
    assert _get_internal_url(hass, allow_ip=False) == "http://example.local:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_current_request=True)

    with patch(
        "homeassistant.helpers.network._get_request_host", return_value="example.local"
    ):
        assert (
            _get_internal_url(hass, require_current_request=True)
            == "http://example.local:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(
                hass, require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(hass, require_current_request=True, require_ssl=True)

    with (
        patch(
            "homeassistant.helpers.network._get_request_host",
            return_value="no_match.example.local",
        ),
        pytest.raises(NoURLAvailableError),
    ):
        _get_internal_url(hass, require_current_request=True)

    # Test with internal URL: https://example.local:8123
    await async_process_ha_core_config(
        hass,
        {"internal_url": "https://example.local:8123"},
    )

    assert hass.config.internal_url == "https://example.local:8123"
    assert _get_internal_url(hass) == "https://example.local:8123"
    assert _get_internal_url(hass, allow_ip=False) == "https://example.local:8123"
    assert _get_internal_url(hass, require_ssl=True) == "https://example.local:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_standard_port=True)

    # Test with internal URL: http://example.local:80/
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:80/"},
    )

    assert hass.config.internal_url == "http://example.local:80/"
    assert _get_internal_url(hass) == "http://example.local"
    assert _get_internal_url(hass, allow_ip=False) == "http://example.local"
    assert _get_internal_url(hass, require_standard_port=True) == "http://example.local"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_ssl=True)

    # Test with internal URL: https://example.local:443
    await async_process_ha_core_config(
        hass,
        {"internal_url": "https://example.local:443"},
    )

    assert hass.config.internal_url == "https://example.local:443"
    assert _get_internal_url(hass) == "https://example.local"
    assert _get_internal_url(hass, allow_ip=False) == "https://example.local"
    assert (
        _get_internal_url(hass, require_standard_port=True) == "https://example.local"
    )
    assert _get_internal_url(hass, require_ssl=True) == "https://example.local"

    # Test with internal URL: https://192.168.0.1
    await async_process_ha_core_config(
        hass,
        {"internal_url": "https://192.168.0.1"},
    )

    assert hass.config.internal_url == "https://192.168.0.1"
    assert _get_internal_url(hass) == "https://192.168.0.1"
    assert _get_internal_url(hass, require_standard_port=True) == "https://192.168.0.1"
    assert _get_internal_url(hass, require_ssl=True) == "https://192.168.0.1"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, allow_ip=False)

    # Test with internal URL: http://192.168.0.1:8123
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://192.168.0.1:8123"},
    )

    assert hass.config.internal_url == "http://192.168.0.1:8123"
    assert _get_internal_url(hass) == "http://192.168.0.1:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(hass, allow_ip=False)

    with patch(
        "homeassistant.helpers.network._get_request_host", return_value="192.168.0.1"
    ):
        assert (
            _get_internal_url(hass, require_current_request=True)
            == "http://192.168.0.1:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(hass, require_current_request=True, allow_ip=False)

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(
                hass, require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(hass, require_current_request=True, require_ssl=True)