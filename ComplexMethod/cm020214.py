async def test_device_info_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_pynecil: AsyncMock,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test device info gets updated."""

    mock_pynecil.get_device_info.return_value = DeviceInfoResponse()
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, config_entry.unique_id)}
    )
    assert device
    assert device.sw_version is None
    assert device.serial_number is None

    mock_pynecil.get_device_info.return_value = DeviceInfoResponse(
        build="v2.22",
        device_id="c0ffeeC0",
        address="c0:ff:ee:c0:ff:ee",
        device_sn="0000c0ffeec0ffee",
        name=DEFAULT_NAME,
    )

    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, config_entry.unique_id)}
    )
    assert device
    assert device.sw_version == "v2.22"
    assert device.serial_number == "0000c0ffeec0ffee (ID:c0ffeeC0)"