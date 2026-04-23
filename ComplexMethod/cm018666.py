async def test_disabled_device_no_coordinator(
    hass: HomeAssistant,
    mock_roborock_entry: MockConfigEntry,
    device_registry: DeviceRegistry,
    fake_devices: list[FakeDevice],
) -> None:
    """Test that a disabled device is registered but no coordinator is created."""
    # Pre-create the first device as disabled so that async_get_or_create
    # finds it already disabled when async_setup_entry runs.
    first_device = fake_devices[0]
    device_registry.async_get_or_create(
        config_entry_id=mock_roborock_entry.entry_id,
        identifiers={(DOMAIN, first_device.duid)},
        name=first_device.device_info.name,
        manufacturer="Roborock",
        disabled_by=dr.DeviceEntryDisabler.USER,
    )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_roborock_entry.state is ConfigEntryState.LOADED

    # The disabled device should still be registered in the device registry
    disabled_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, first_device.duid)}
    )
    assert disabled_device_entry is not None
    assert disabled_device_entry.disabled

    # No coordinator should have been created for the disabled device,
    # so no entities should exist for it.
    coordinators = mock_roborock_entry.runtime_data
    assert all(coord.duid != first_device.duid for coord in coordinators.v1)

    # Other devices should still be set up
    found_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    enabled_device_names = {
        device.name for device in found_devices if not device.disabled
    }
    assert "Roborock S7 MaxV" not in enabled_device_names
    assert "Roborock S7 2" in enabled_device_names