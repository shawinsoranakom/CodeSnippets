async def test_alexa_config_report_state(
    hass: HomeAssistant, cloud_prefs: CloudPreferences, cloud_stub: Mock
) -> None:
    """Test Alexa config should expose using prefs."""
    assert await async_setup_component(hass, "homeassistant", {})

    await cloud_prefs.async_update(
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs, cloud_stub
    )
    await conf.async_initialize()
    await conf.set_authorized(True)

    assert cloud_prefs.alexa_report_state is False
    assert conf.should_report_state is False
    assert conf.is_reporting_states is False

    with patch.object(conf, "async_get_access_token", AsyncMock(return_value="hello")):
        await cloud_prefs.async_update(alexa_report_state=True)
        await hass.async_block_till_done()

    assert cloud_prefs.alexa_report_state is True
    assert conf.should_report_state is True
    assert conf.is_reporting_states is True

    await cloud_prefs.async_update(alexa_report_state=False)
    await hass.async_block_till_done()

    assert cloud_prefs.alexa_report_state is False
    assert conf.should_report_state is False
    assert conf.is_reporting_states is False