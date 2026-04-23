async def test_update_suggested_area(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    area_registry: ar.AreaRegistry,
    mock_config_entry: MockConfigEntry,
    initial_area: str | None,
    device_area_id: str | None,
    number_of_areas: int,
) -> None:
    """Verify that we can update the suggested area of a device.

    Updating the suggested area of a device should not create a new area, nor should
    it change the area_id of the device.
    """
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bla", "123")},
        suggested_area=initial_area,
    )
    assert entry.area_id == device_area_id

    suggested_area = "Pool"

    with patch.object(device_registry, "async_schedule_save") as mock_save:
        updated_entry = device_registry.async_update_device(
            entry.id, suggested_area=suggested_area
        )

    # Check the device registry was not saved
    assert mock_save.call_count == 0
    assert updated_entry != entry
    assert updated_entry.area_id == device_area_id

    # Check we did not create an area
    pool_area = area_registry.async_get_area_by_name(suggested_area)
    assert pool_area is None
    assert updated_entry.area_id == device_area_id
    assert len(area_registry.areas) == number_of_areas

    await hass.async_block_till_done()

    assert len(update_events) == 1
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }

    # Do not save or fire the event if the suggested
    # area does not result in a change of area
    # but still update the actual entry
    with patch.object(device_registry, "async_schedule_save") as mock_save_2:
        updated_entry = device_registry.async_update_device(
            entry.id, suggested_area="Other"
        )
    assert len(update_events) == 1
    assert mock_save_2.call_count == 0
    assert updated_entry != entry
    assert updated_entry.area_id == device_area_id