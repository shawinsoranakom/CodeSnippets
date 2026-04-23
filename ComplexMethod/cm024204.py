async def help_test_entity_device_info_with_connection(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
) -> None:
    """Test device registry integration.

    This is a test helper for the MqttDiscoveryUpdate mixin.
    """
    await mqtt_mock_entry()
    # Add device settings to config
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    config["device"] = copy.deepcopy(DEFAULT_CONFIG_DEVICE_INFO_MAC)
    config["unique_id"] = "veryunique"

    area_registry = ar.async_get(hass)
    device_registry = dr.async_get(hass)

    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12")}
    )
    assert device is not None
    assert device.connections == {(dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12")}
    assert device.manufacturer == "Whatever"
    assert device.name == "Beer"
    assert device.model == "Glass"
    assert device.model_id == "XYZ001"
    assert device.hw_version == "rev1"
    assert device.sw_version == "0.1-beta"
    assert device.area_id == area_registry.async_get_area_by_name("default_area").id
    assert device.configuration_url == "http://example.com"