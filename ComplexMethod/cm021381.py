async def test_device_setup_registry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we register the device and the entries correctly."""
    device = get_device("Office")

    mock_setup = await device.setup_entry(hass)
    await hass.async_block_till_done()

    assert len(device_registry.devices) == 1

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    assert device_entry.identifiers == {(DOMAIN, device.mac)}
    assert device_entry.name == device.name
    assert device_entry.model == device.model
    assert device_entry.manufacturer == device.manufacturer
    assert device_entry.sw_version == device.fwversion

    for entry in er.async_entries_for_device(entity_registry, device_entry.id):
        assert (
            hass.states.get(entry.entity_id)
            .attributes[ATTR_FRIENDLY_NAME]
            .startswith(device.name)
        )