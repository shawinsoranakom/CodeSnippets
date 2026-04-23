async def help_test_discovery_removal(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    caplog: pytest.LogCaptureFixture,
    domain: str,
    config1: dict[str, Any],
    config2: dict[str, Any],
    sensor_config1: dict[str, Any] | None = None,
    sensor_config2: dict[str, Any] | None = None,
    object_id: str = "tasmota_test",
    name: str = "Tasmota Test",
) -> None:
    """Test removal of discovered entity."""
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    assert config1[CONF_MAC] == config2[CONF_MAC]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config1[CONF_MAC]}/config", data1)
    await hass.async_block_till_done()
    if sensor_config1:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config1[CONF_MAC]}/sensors",
            json.dumps(sensor_config1),
        )
        await hass.async_block_till_done()

    # Verify device and entity registry entries are created
    device_entry = device_reg.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, config1[CONF_MAC])}
    )
    assert device_entry is not None
    entity_entry = entity_reg.async_get(f"{domain}.{object_id}")
    assert entity_entry is not None

    # Verify state is added
    state = hass.states.get(f"{domain}.{object_id}")
    assert state is not None
    assert state.name == name

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config2[CONF_MAC]}/config", data2)
    await hass.async_block_till_done()
    if sensor_config1:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config2[CONF_MAC]}/sensors",
            json.dumps(sensor_config2),
        )
        await hass.async_block_till_done()

    # Verify entity registry entries are cleared
    device_entry = device_reg.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, config2[CONF_MAC])}
    )
    assert device_entry is not None
    entity_entry = entity_reg.async_get(f"{domain}.{object_id}")
    assert entity_entry is None

    # Verify state is removed
    state = hass.states.get(f"{domain}.{object_id}")
    assert state is None