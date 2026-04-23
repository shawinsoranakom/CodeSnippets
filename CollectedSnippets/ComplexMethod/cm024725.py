async def test_reload_service(
    hass: HomeAssistant, load_yaml_integration: None, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reload serviice."""

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()

    state_binary_sensor = hass.states.get("binary_sensor.test")
    state_sensor = hass.states.get("sensor.test")
    assert state_binary_sensor.state == STATE_ON
    assert state_sensor.state == "5"

    caplog.clear()

    yaml_path = get_fixture_path("configuration.yaml", "command_line")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert "Loading config" in caplog.text

    state_binary_sensor = hass.states.get("binary_sensor.test")
    state_sensor = hass.states.get("sensor.test")
    assert state_binary_sensor.state == STATE_ON
    assert not state_sensor

    caplog.clear()

    yaml_path = get_fixture_path("configuration_empty.yaml", "command_line")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    state_binary_sensor = hass.states.get("binary_sensor.test")
    state_sensor = hass.states.get("sensor.test")
    assert not state_binary_sensor
    assert not state_sensor

    assert "Loading config" not in caplog.text