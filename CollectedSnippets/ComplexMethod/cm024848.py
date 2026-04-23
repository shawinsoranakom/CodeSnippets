async def test_is_internal_request(hass: HomeAssistant, mock_current_request) -> None:
    """Test if accessing an instance on its internal URL."""
    # Test with internal URL: http://example.local:8123
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )

    assert hass.config.internal_url == "http://example.local:8123"

    # No request active
    mock_current_request.return_value = None
    assert not is_internal_request(hass)

    mock_current_request.return_value = Mock(
        headers=CIMultiDictProxy(CIMultiDict({hdrs.HOST: "example.local:8123"})),
        host="example.local:8123",
        url=URL("http://example.local:8123"),
    )
    assert is_internal_request(hass)

    mock_current_request.return_value = Mock(
        headers=CIMultiDictProxy(
            CIMultiDict({hdrs.HOST: "no_match.example.local:8123"})
        ),
        host="no_match.example.local:8123",
        url=URL("http://no_match.example.local:8123"),
    )
    assert not is_internal_request(hass)

    # Test with internal URL: http://192.168.0.1:8123
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://192.168.0.1:8123"},
    )

    assert hass.config.internal_url == "http://192.168.0.1:8123"
    assert not is_internal_request(hass)

    mock_current_request.return_value = Mock(
        headers=CIMultiDictProxy(CIMultiDict({hdrs.HOST: "192.168.0.1:8123"})),
        host="192.168.0.1:8123",
        url=URL("http://192.168.0.1:8123"),
    )
    assert is_internal_request(hass)

    # Test for matching against local IP
    hass.config.api = Mock(use_ssl=False, local_ip="192.168.123.123", port=8123)
    for allowed in ("127.0.0.1", "192.168.123.123"):
        mock_current_request.return_value = Mock(
            headers=CIMultiDictProxy(CIMultiDict({hdrs.HOST: f"{allowed}:8123"})),
            host=f"{allowed}:8123",
            url=URL(f"http://{allowed}:8123"),
        )
        assert is_internal_request(hass), mock_current_request.return_value.url

    # Test for matching against HassOS hostname
    for allowed in ("hellohost", "hellohost.local"):
        mock_current_request.return_value = Mock(
            headers=CIMultiDictProxy(CIMultiDict({hdrs.HOST: f"{allowed}:8123"})),
            host=f"{allowed}:8123",
            url=URL(f"http://{allowed}:8123"),
        )
        assert is_internal_request(hass), mock_current_request.return_value.url