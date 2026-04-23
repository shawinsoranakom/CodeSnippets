async def test_auto_remove_devices(
    hass: HomeAssistant,
    device_registry: DeviceRegistry,
    mock_added_config_entry: MockConfigEntry,
    user: User,
    controller: Controller,
    zones: list[Zone],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test old devices are auto-removed from the device registry."""
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, str(controller.id))})
        is not None
    )
    for zone in zones:
        device = device_registry.async_get_device(identifiers={(DOMAIN, str(zone.id))})
        assert device is not None

    user.controllers = []
    # Make the coordinator refresh data.
    freezer.tick(MAIN_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, str(controller.id))})
        is None
    )
    for zone in zones:
        device = device_registry.async_get_device(identifiers={(DOMAIN, str(zone.id))})
        assert device is None
    all_devices = dr.async_entries_for_config_entry(
        device_registry, mock_added_config_entry.entry_id
    )
    assert len(all_devices) == 0