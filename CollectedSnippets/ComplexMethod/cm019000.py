async def test_update_firmware(
    hass: HomeAssistant,
    mock_device: MockDevice,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test updating a device."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id = f"{UPDATE_DOMAIN}.{device_name}_firmware"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id) == snapshot
    assert entity_registry.async_get(entity_id) == snapshot

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert mock_device.device.async_start_firmware_update.call_count == 1

    # Emulate state change
    mock_device.firmware_version = FIRMWARE_UPDATE_AVAILABLE.new_firmware_version.split(
        "_"
    )[0]
    mock_device.device.async_check_firmware_available.return_value = (
        UpdateFirmwareCheck(result=UPDATE_NOT_AVAILABLE)
    )
    freezer.tick(FIRMWARE_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF

    device_info = device_registry.async_get_device(
        {(DOMAIN, mock_device.serial_number)}
    )
    assert device_info is not None
    assert device_info.sw_version == mock_device.firmware_version