async def test_alexa_config_invalidate_token(
    hass: HomeAssistant,
    cloud_prefs: CloudPreferences,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test Alexa config should expose using prefs."""
    assert await async_setup_component(hass, "homeassistant", {})

    aioclient_mock.post(
        "https://example/alexa/access_token",
        json={
            "access_token": "mock-token",
            "event_endpoint": "http://example.com/alexa_endpoint",
            "expires_in": 30,
        },
    )
    conf = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
        "mock-user-id",
        cloud_prefs,
        Mock(
            servicehandlers_server="example",
            auth=Mock(async_check_token=AsyncMock()),
            websession=async_get_clientsession(hass),
            alexa_api=Mock(
                access_token=AsyncMock(
                    return_value={
                        "access_token": "mock-token",
                        "event_endpoint": "http://example.com/alexa_endpoint",
                        "expires_in": 30,
                    }
                )
            ),
        ),
    )

    token = await conf.async_get_access_token()
    assert token == "mock-token"
    assert len(conf._cloud.alexa_api.access_token.mock_calls) == 1

    token = await conf.async_get_access_token()
    assert token == "mock-token"
    assert len(conf._cloud.alexa_api.access_token.mock_calls) == 1
    assert conf._token_valid is not None
    conf.async_invalidate_access_token()
    assert conf._token_valid is None
    token = await conf.async_get_access_token()
    assert token == "mock-token"
    assert len(conf._cloud.alexa_api.access_token.mock_calls) == 2