async def test_device_info(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test device info."""
    entry = await setup_platform(hass, aioclient_mock, SENSOR_DOMAIN)

    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})

    assert device.configuration_url == "https://engage.efergy.com/user/login"
    assert device.connections == {("mac", "ff:ff:ff:ff:ff:ff")}
    assert device.identifiers == {(DOMAIN, entry.entry_id)}
    assert device.manufacturer == DEFAULT_NAME
    assert device.model == "EEEHub"
    assert device.name == DEFAULT_NAME
    assert device.sw_version == "2.3.7"