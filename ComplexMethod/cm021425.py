async def test_auto_add_devices(
    hass: HomeAssistant,
    device_registry: DeviceRegistry,
    mock_added_config_entry: MockConfigEntry,
    mock_pydrawise: AsyncMock,
    user: User,
    controller: Controller,
    zones: list[Zone],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test new devices are auto-added to the device registry."""
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, str(controller.id))}
    )
    assert device is not None
    for zone in zones:
        zone_device = device_registry.async_get_device(
            identifiers={(DOMAIN, str(zone.id))}
        )
        assert zone_device is not None
    all_devices = dr.async_entries_for_config_entry(
        device_registry, mock_added_config_entry.entry_id
    )
    # 1 controller + 2 zones
    assert len(all_devices) == 3

    controller2 = deepcopy(controller)
    controller2.id += 10
    controller2.name += " 2"
    controller2.sensors = []

    zones2 = deepcopy(zones)
    for zone in zones2:
        zone.id += 10
        zone.name += " 2"

    user.controllers = [controller, controller2]
    mock_pydrawise.get_zones.side_effect = [zones, zones2]

    # Make the coordinator refresh data.
    freezer.tick(MAIN_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    new_controller_device = device_registry.async_get_device(
        identifiers={(DOMAIN, str(controller2.id))}
    )
    assert new_controller_device is not None
    for zone in zones2:
        new_zone_device = device_registry.async_get_device(
            identifiers={(DOMAIN, str(zone.id))}
        )
        assert new_zone_device is not None

    all_devices = dr.async_entries_for_config_entry(
        device_registry, mock_added_config_entry.entry_id
    )
    # 2 controllers + 4 zones
    assert len(all_devices) == 6