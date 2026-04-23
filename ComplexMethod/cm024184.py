async def test_clear_config_topic_disabled_entity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the discovery topic is removed when a disabled entity is removed."""
    mqtt_mock = await mqtt_mock_entry()
    # discover an entity that is not enabled by default
    config = {
        "state_topic": "homeassistant_test/sensor/sbfspot_0/sbfspot_12345/",
        "unique_id": "sbfspot_12345",
        "enabled_by_default": False,
        "device": {
            "identifiers": ["sbfspot_12345"],
            "name": "abc123",
            "sw_version": "1.0",
            "connections": [["mac", "12:34:56:AB:CD:EF"]],
        },
    }
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/sbfspot_12345/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    # discover an entity that is not unique (part 1), will be added
    config_not_unique1 = copy.deepcopy(config)
    config_not_unique1["name"] = "sbfspot_12345_1"
    config_not_unique1["unique_id"] = "not_unique"
    config_not_unique1.pop("enabled_by_default")
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/sbfspot_12345_1/config",
        json.dumps(config_not_unique1),
    )
    # discover an entity that is not unique (part 2), will not be added
    config_not_unique2 = copy.deepcopy(config_not_unique1)
    config_not_unique2["name"] = "sbfspot_12345_2"
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/sbfspot_12345_2/config",
        json.dumps(config_not_unique2),
    )
    await hass.async_block_till_done()
    assert "Platform mqtt does not generate unique IDs" in caplog.text

    assert hass.states.get("sensor.abc123_sbfspot_12345") is None  # disabled
    assert hass.states.get("sensor.abc123_sbfspot_12345_1") is not None  # enabled
    assert hass.states.get("sensor.abc123_sbfspot_12345_2") is None  # not unique

    # Verify device is created
    device_entry = device_registry.async_get_device(
        connections={("mac", "12:34:56:AB:CD:EF")}
    )
    assert device_entry is not None

    # Remove the device from the registry
    device_registry.async_remove_device(device_entry.id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Assert all valid discovery topics are cleared
    assert mqtt_mock.async_publish.call_count == 2
    assert (
        call("homeassistant/sensor/sbfspot_0/sbfspot_12345/config", None, 0, True)
        in mqtt_mock.async_publish.mock_calls
    )
    assert (
        call("homeassistant/sensor/sbfspot_0/sbfspot_12345_1/config", None, 0, True)
        in mqtt_mock.async_publish.mock_calls
    )