async def test_correct_config_discovery_component(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
    discovery_topic: str,
    discovery_hash: tuple[str, str],
) -> None:
    """Test sending in correct JSON."""
    await mqtt_mock_entry()
    config_init = {
        "name": "Beer",
        "state_topic": "test-topic",
        "unique_id": "bla001",
        "device": {"identifiers": "0AFFD2", "name": "test_device1"},
        "o": {"name": "foobar"},
    }
    async_fire_mqtt_message(
        hass,
        discovery_topic,
        json.dumps(config_init),
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_device1_beer")

    assert state is not None
    assert state.name == "test_device1 Beer"
    assert discovery_hash in hass.data["mqtt"].discovery_already_discovered

    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    assert device_entry.name == "test_device1"

    # Update the device and component
    config_update = {
        "name": "Milk",
        "state_topic": "test-topic",
        "unique_id": "bla001",
        "device": {"identifiers": "0AFFD2", "name": "test_device2"},
        "o": {"name": "foobar"},
    }
    async_fire_mqtt_message(
        hass,
        discovery_topic,
        json.dumps(config_update),
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_device1_beer")

    assert state is not None
    assert state.name == "test_device2 Milk"
    assert discovery_hash in hass.data["mqtt"].discovery_already_discovered

    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    assert device_entry.name == "test_device2"

    # Remove the device and component
    async_fire_mqtt_message(
        hass,
        discovery_topic,
        "",
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_device1_beer")

    assert state is None

    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None