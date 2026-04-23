async def test_setup_registers_hub_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """The hub device is registered with the expected metadata."""
    entry = _make_entry(hass, auto_discovered=False)
    hub = _make_hub_mock()
    with patch("homeassistant.components.nobo_hub.nobo") as mock_cls:
        mock_cls.return_value = hub
        mock_cls.async_discover_hubs = AsyncMock(return_value=set())
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, SERIAL)})
    assert device is not None
    assert device.config_entries == {entry.entry_id}
    assert device.name == "My Eco Hub"
    assert device.manufacturer == "Glen Dimplex Nordic AS"
    assert device.model == "Nobø Ecohub"
    assert device.serial_number == SERIAL
    assert device.sw_version == "115"
    assert device.hw_version == "hw"