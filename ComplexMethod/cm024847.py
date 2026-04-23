async def test_get_url(hass: HomeAssistant) -> None:
    """Test getting an instance URL."""
    assert hass.config.external_url is None
    assert hass.config.internal_url is None

    with pytest.raises(NoURLAvailableError):
        get_url(hass)

    hass.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")
    assert get_url(hass) == "http://192.168.123.123:8123"
    assert get_url(hass, prefer_external=True) == "http://192.168.123.123:8123"

    with pytest.raises(NoURLAvailableError):
        get_url(hass, allow_internal=False)

    # Test only external
    hass.config.api = None
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )
    assert hass.config.external_url == "https://example.com"
    assert hass.config.internal_url is None
    assert get_url(hass) == "https://example.com"

    # Test preference or allowance
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local", "external_url": "https://example.com"},
    )
    assert hass.config.external_url == "https://example.com"
    assert hass.config.internal_url == "http://example.local"
    assert get_url(hass) == "http://example.local"
    assert get_url(hass, prefer_external=True) == "https://example.com"
    assert get_url(hass, allow_internal=False) == "https://example.com"
    assert (
        get_url(hass, prefer_external=True, allow_external=False)
        == "http://example.local"
    )
    # Prefer external defaults to True if use_ssl=True
    hass.config.api = Mock(use_ssl=True)
    assert get_url(hass) == "https://example.com"
    hass.config.api = Mock(use_ssl=False)
    assert get_url(hass) == "http://example.local"
    hass.config.api = None

    with pytest.raises(NoURLAvailableError):
        get_url(hass, allow_external=False, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        get_url(hass, allow_external=False, allow_internal=False)

    with pytest.raises(NoURLAvailableError):
        get_url(hass, require_current_request=True)

    with (
        patch(
            "homeassistant.helpers.network._get_request_host",
            return_value="example.com",
        ),
        patch("homeassistant.helpers.http.current_request"),
    ):
        assert get_url(hass, require_current_request=True) == "https://example.com"
        assert (
            get_url(hass, require_current_request=True, require_ssl=True)
            == "https://example.com"
        )

        with pytest.raises(NoURLAvailableError):
            get_url(hass, require_current_request=True, allow_external=False)

    with (
        patch(
            "homeassistant.helpers.network._get_request_host",
            return_value="example.local",
        ),
        patch("homeassistant.helpers.http.current_request"),
    ):
        assert get_url(hass, require_current_request=True) == "http://example.local"

        with pytest.raises(NoURLAvailableError):
            get_url(hass, require_current_request=True, allow_internal=False)

        with pytest.raises(NoURLAvailableError):
            get_url(hass, require_current_request=True, require_ssl=True)

    with (
        patch(
            "homeassistant.helpers.network._get_request_host",
            return_value="no_match.example.com",
        ),
        pytest.raises(NoURLAvailableError),
    ):
        _get_internal_url(hass, require_current_request=True)

    # Test allow_ip defaults when SSL specified
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://1.1.1.1"},
    )
    assert hass.config.external_url == "https://1.1.1.1"
    assert get_url(hass, allow_internal=False) == "https://1.1.1.1"
    hass.config.api = Mock(use_ssl=False)
    assert get_url(hass, allow_internal=False) == "https://1.1.1.1"
    hass.config.api = Mock(use_ssl=True)
    with pytest.raises(NoURLAvailableError):
        assert get_url(hass, allow_internal=False)