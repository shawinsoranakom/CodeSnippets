async def test_default_setup(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test all basic functionality of the rflink sensor component."""
    # setup mocking rflink module
    event_callback, create, _, _ = await mock_rflink(hass, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of sensor loaded from config
    config_sensor = hass.states.get("binary_sensor.test")
    assert config_sensor
    assert config_sensor.state == STATE_UNKNOWN
    assert config_sensor.attributes["device_class"] == "door"

    # test on event for config sensor
    event_callback({"id": "test", "command": "on"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.test").state == STATE_ON

    # test off event for config sensor
    event_callback({"id": "test", "command": "off"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.test").state == STATE_OFF

    # test allon event for config sensor
    event_callback({"id": "test", "command": "allon"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.test").state == STATE_ON

    # test alloff event for config sensor
    event_callback({"id": "test", "command": "alloff"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.test").state == STATE_OFF