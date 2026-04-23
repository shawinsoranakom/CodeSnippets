async def test_alexa_config(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test all methods of the AlexaConfig class."""
    config = {
        "filter": entityfilter.FILTER_SCHEMA({"include_domains": ["sensor"]}),
    }
    test_config = smart_home.AlexaConfig(hass, config)
    await test_config.async_initialize()
    assert not test_config.supports_auth
    assert not test_config.should_report_state
    assert test_config.endpoint is None
    assert test_config.entity_config == {}
    assert test_config.user_identifier() == ""
    assert test_config.locale is None
    assert test_config.should_expose("sensor.test")
    assert not test_config.should_expose("switch.test")
    with patch.object(test_config, "_auth", AsyncMock()):
        test_config._auth.async_invalidate_access_token = MagicMock()
        test_config.async_invalidate_access_token()
        assert len(test_config._auth.async_invalidate_access_token.mock_calls) == 1
        await test_config.async_accept_grant("grant_code")
        test_config._auth.async_do_auth.assert_called_once_with("grant_code")