async def test_device_registry_migration(
    hass: HomeAssistant,
    legacy_dev_reg_entry: dr.DeviceEntry,
    voip_devices: VoIPDevices,
    call_info: CallInfo,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test info in device registry migrates old devices."""
    voip_device = voip_devices.async_get_or_create(call_info)
    new_id = call_info.caller_endpoint.uri
    assert voip_device.voip_id == new_id

    device = device_registry.async_get_device(identifiers={(DOMAIN, new_id)})
    assert device is not None
    assert device.id == legacy_dev_reg_entry.id
    assert device.identifiers == {(DOMAIN, new_id)}
    assert device.name == call_info.caller_endpoint.host
    assert device.manufacturer == "Grandstream"
    assert device.model == "HT801"
    assert device.sw_version == "1.0.17.5"

    assert (
        entity_registry.async_get_entity_id("switch", DOMAIN, f"{new_id}-allow_calls")
        is not None
    )