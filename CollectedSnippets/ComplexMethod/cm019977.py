async def test_oven_core_probe_sensors_unknown_when_inactive(
    hass: HomeAssistant,
    mock_miele_client: MagicMock,
    setup_platform: None,
    device_fixture: MieleDevices,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Oven food-probe (core) sensors must not expose API inactive sentinels as temperatures.

    Miele uses raw value -32768 (centidegrees) when the probe is not in use. After the
    probe has reported a valid reading once, those entities must stay in the UI but
    their state must be unknown—not a bogus numeric temperature.
    """
    core_temp = "sensor.oven_core_temperature"
    core_target = "sensor.oven_core_target_temperature"

    assert hass.states.get(core_temp) is None
    assert hass.states.get(core_target) is None

    device_fixture["DummyOven"]["state"]["coreTargetTemperature"][0]["value_raw"] = 3000
    device_fixture["DummyOven"]["state"]["coreTargetTemperature"][0][
        "value_localized"
    ] = 30.0
    device_fixture["DummyOven"]["state"]["coreTemperature"][0]["value_raw"] = 2200
    device_fixture["DummyOven"]["state"]["coreTemperature"][0]["value_localized"] = 22.0

    freezer.tick(timedelta(seconds=130))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(core_temp) is not None
    assert hass.states.get(core_temp).state == "22.0"
    assert hass.states.get(core_target) is not None
    assert hass.states.get(core_target).state == "30.0"

    device_fixture["DummyOven"]["state"]["coreTargetTemperature"][0][
        "value_raw"
    ] = -32768
    device_fixture["DummyOven"]["state"]["coreTargetTemperature"][0][
        "value_localized"
    ] = None
    device_fixture["DummyOven"]["state"]["coreTemperature"][0]["value_raw"] = -32768
    device_fixture["DummyOven"]["state"]["coreTemperature"][0]["value_localized"] = None

    freezer.tick(timedelta(seconds=130))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(core_temp).state == STATE_UNKNOWN
    assert hass.states.get(core_target).state == STATE_UNKNOWN