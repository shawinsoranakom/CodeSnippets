async def test_device_info(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
) -> None:
    """Test device information populates correctly."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    device = device_registry.async_get_device({(DOMAIN, "1")})
    assert device is not None
    assert device.manufacturer == "HEOS"
    assert device.model == "Drive HS2"
    assert device.name == "Test Player"
    assert device.serial_number == "123456"
    assert device.sw_version == "1.0.0"
    device = device_registry.async_get_device({(DOMAIN, "2")})
    assert device is not None
    assert device.manufacturer == "HEOS"
    assert device.model == "Speaker"