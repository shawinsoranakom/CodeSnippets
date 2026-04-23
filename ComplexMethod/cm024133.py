async def test_turn_on_and_off_without_power_command(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    climate_on: str | None,
    climate_off: str | None,
) -> None:
    """Test setting of turn on/off with power command enabled."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "off"

    await common.async_turn_on(hass, ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert climate_on is None or state.state == climate_on
    if climate_on:
        mqtt_mock.async_publish.assert_has_calls(
            [call("mode-topic", climate_on, 0, False)]
        )
    else:
        mqtt_mock.async_publish.assert_has_calls([])

    await common.async_set_hvac_mode(hass, HVACMode.COOL, ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"
    mqtt_mock.async_publish.reset_mock()

    if climate_off:
        await common.async_turn_off(hass, ENTITY_CLIMATE)
        state = hass.states.get(ENTITY_CLIMATE)
        assert climate_off is None or state.state == climate_off
        assert state.state == "off"
        mqtt_mock.async_publish.assert_has_calls([call("mode-topic", "off", 0, False)])
    else:
        assert state.state == "cool"
        mqtt_mock.async_publish.assert_has_calls([])
    mqtt_mock.async_publish.reset_mock()