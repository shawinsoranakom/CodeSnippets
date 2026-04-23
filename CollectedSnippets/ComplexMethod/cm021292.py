async def test_default_setup(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test all basic functionality of the rflink sensor component."""
    # setup mocking rflink module
    event_callback, create, _, _ = await mock_rflink(hass, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of sensor loaded from config
    config_sensor = hass.states.get("sensor.test")
    assert config_sensor
    assert config_sensor.state == "unknown"
    assert (
        config_sensor.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    )

    # test event for config sensor
    event_callback(
        {
            "id": "test",
            "sensor": "temperature",
            "value": 1,
            "unit": UnitOfTemperature.CELSIUS,
        }
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test").state == "1"

    # test event for new unconfigured sensor
    event_callback(
        {
            "id": "test2",
            "sensor": "temperature",
            "value": 0,
            "unit": UnitOfTemperature.CELSIUS,
        }
    )
    await hass.async_block_till_done()

    # test state of temp sensor
    temp_sensor = hass.states.get("sensor.test2")
    assert temp_sensor
    assert temp_sensor.state == "0"
    assert temp_sensor.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert (
        ATTR_ICON not in temp_sensor.attributes
    )  # temperature uses SensorEntityDescription

    # test event for new unconfigured sensor
    event_callback({"id": "test3", "sensor": "battery", "value": "ok", "unit": None})
    await hass.async_block_till_done()

    # test state of battery sensor
    bat_sensor = hass.states.get("sensor.test3")
    assert bat_sensor
    assert bat_sensor.state == "ok"
    assert ATTR_UNIT_OF_MEASUREMENT not in bat_sensor.attributes
    assert bat_sensor.attributes[ATTR_ICON] == "mdi:battery"