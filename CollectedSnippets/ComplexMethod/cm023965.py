async def test_integration_reload(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_modbus,
) -> None:
    """Run test for integration reload."""

    caplog.set_level(logging.DEBUG)
    caplog.clear()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()

    yaml_path = get_fixture_path("configuration.yaml", DOMAIN)
    with mock.patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()
    assert "Modbus reloading" in caplog.text
    state_sensor_1 = hass.states.get("sensor.dummy")
    state_sensor_2 = hass.states.get("sensor.dummy_2")
    assert state_sensor_1
    assert not state_sensor_2

    caplog.clear()
    yaml_path = get_fixture_path("configuration_2.yaml", DOMAIN)
    with mock.patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()
    assert "Modbus reloading" in caplog.text
    state_sensor_1 = hass.states.get("sensor.dummy")
    state_sensor_2 = hass.states.get("sensor.dummy_2")
    assert state_sensor_1
    assert state_sensor_2

    caplog.clear()
    yaml_path = get_fixture_path("configuration_empty.yaml", DOMAIN)
    with mock.patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()
    assert "Modbus not present anymore" in caplog.text
    state_sensor_1 = hass.states.get("sensor.dummy")
    state_sensor_2 = hass.states.get("sensor.dummy_2")
    assert not state_sensor_1
    assert not state_sensor_2