async def test_migration_from_v1_with_baudrate(
    hass: HomeAssistant, config_entry_v1
) -> None:
    """Test migration of config entry from v1 with baudrate in config."""
    config_entry_v1.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_BAUDRATE: 115200}})

    assert config_entry_v1.data[CONF_RADIO_TYPE] == DATA_RADIO_TYPE
    assert CONF_DEVICE in config_entry_v1.data
    assert config_entry_v1.data[CONF_DEVICE][CONF_DEVICE_PATH] == DATA_PORT_PATH
    assert CONF_USB_PATH not in config_entry_v1.data
    assert CONF_BAUDRATE in config_entry_v1.data[CONF_DEVICE]
    assert config_entry_v1.data[CONF_DEVICE][CONF_BAUDRATE] == 115200
    assert config_entry_v1.version == 5