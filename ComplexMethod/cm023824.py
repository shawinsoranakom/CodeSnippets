async def test_setup_smart_by_bond_fan(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test setting up a fan without a hub."""
    config_entry = await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        bond_version={
            "bondid": "KXXX12345",
            "target": "test-model",
            "fw_ver": "test-version",
            "mcu_ver": "test-hw-version",
        },
    )
    assert hass.states.get("fan.name_1") is not None
    entry = entity_registry.async_get("fan.name_1")
    assert entry.device_id is not None
    device = device_registry.async_get(entry.device_id)
    assert device is not None
    assert device.sw_version == "test-version"
    assert device.manufacturer == "Olibra"
    assert device.identifiers == {("bond", "KXXX12345", "test-device-id")}
    assert device.hw_version == "test-hw-version"
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()