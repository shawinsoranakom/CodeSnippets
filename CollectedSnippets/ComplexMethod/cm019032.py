async def test_alexa_config_fail_refresh_token(
    hass: HomeAssistant,
    cloud_prefs: CloudPreferences,
    aioclient_mock: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
    lib_exception: Exception,
    expected_exception: type[Exception],
) -> None:
    """Test Alexa config failing to refresh token."""
    assert await async_setup_component(hass, "homeassistant", {})
    # Enable exposing new entities to Alexa
    expose_new(hass, True)
    # Register a fan entity
    entity_entry = entity_registry.async_get_or_create(
        "fan", "test", "unique", suggested_object_id="test_fan"
    )

    aioclient_mock.post(
        "https://example/alexa/access_token",
        json={
            "access_token": "mock-token",
            "event_endpoint": "http://example.com/alexa_endpoint",
            "expires_in": 30,
        },
    )
    aioclient_mock.post("http://example.com/alexa_endpoint", text="", status=202)
    await cloud_prefs.async_update(
        alexa_report_state=False,
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
    await conf.async_initialize()
    await conf.set_authorized(True)

    assert cloud_prefs.alexa_report_state is False
    assert conf.should_report_state is False
    assert conf.is_reporting_states is False

    hass.states.async_set(entity_entry.entity_id, "off")

    # Enable state reporting
    await cloud_prefs.async_update(alexa_report_state=True)
    await hass.async_block_till_done()

    assert cloud_prefs.alexa_report_state is True
    assert conf.should_report_state is True
    assert conf.is_reporting_states is True

    # Change states to trigger event listener
    hass.states.async_set(entity_entry.entity_id, "on")
    await hass.async_block_till_done()

    # Invalidate the token and try to fetch another
    conf.async_invalidate_access_token()
    conf._cloud.alexa_api.access_token.side_effect = lib_exception

    # Change states to trigger event listener
    hass.states.async_set(entity_entry.entity_id, "off")
    await hass.async_block_till_done()

    # Check state reporting is still wanted in cloud prefs, but disabled for Alexa
    assert cloud_prefs.alexa_report_state is True
    assert conf.should_report_state is False
    assert conf.is_reporting_states is False

    # Simulate we're again authorized, but token update fails
    with pytest.raises(expected_exception):
        await conf.set_authorized(True)

    assert cloud_prefs.alexa_report_state is True
    assert conf.should_report_state is False
    assert conf.is_reporting_states is False

    # Simulate we're again authorized and token update succeeds
    # State reporting should now be re-enabled for Alexa
    conf._cloud.alexa_api.access_token.side_effect = None

    await conf.set_authorized(True)
    assert cloud_prefs.alexa_report_state is True
    assert conf.should_report_state is True
    assert conf.is_reporting_states is True