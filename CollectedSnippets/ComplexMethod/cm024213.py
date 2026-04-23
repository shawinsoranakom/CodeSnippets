async def help_test_reloadable(
    hass: HomeAssistant,
    mqtt_client_mock: MqttMockPahoClient,
    domain: str,
    config: ConfigType,
) -> None:
    """Test reloading an MQTT platform."""
    # Set up with empty config
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    # Create and test an old config of 2 entities based on the config supplied
    old_config_1 = copy.deepcopy(config)
    old_config_1["name"] = "test_old_1"
    old_config_2 = copy.deepcopy(config)
    old_config_2["name"] = "test_old_2"

    old_config = {
        mqtt.DOMAIN: {domain: [old_config_1, old_config_2]},
    }
    # Start the MQTT entry with the old config
    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={mqtt.CONF_BROKER: "test-broker"},
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    mqtt_client_mock.connect.return_value = 0
    with patch("homeassistant.config.load_yaml_config_file", return_value=old_config):
        await hass.config_entries.async_setup(entry.entry_id)

    assert hass.states.get(f"{domain}.test_old_1")
    assert hass.states.get(f"{domain}.test_old_2")
    assert len(hass.states.async_all(domain)) == 2

    # Create temporary fixture for configuration.yaml based on the supplied config and
    # test a reload with this new config
    new_config_1 = copy.deepcopy(config)
    new_config_1["name"] = "test_new_1"
    new_config_2 = copy.deepcopy(config)
    new_config_2["name"] = "test_new_2"
    new_config_extra = copy.deepcopy(config)
    new_config_extra["name"] = "test_new_3"

    new_config = {
        mqtt.DOMAIN: {domain: [new_config_1, new_config_2, new_config_extra]},
    }
    with patch("homeassistant.config.load_yaml_config_file", return_value=new_config):
        # Reload the mqtt entry with the new config
        await hass.services.async_call(
            "mqtt",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_all(domain)) == 3

    assert hass.states.get(f"{domain}.test_new_1")
    assert hass.states.get(f"{domain}.test_new_2")
    assert hass.states.get(f"{domain}.test_new_3")