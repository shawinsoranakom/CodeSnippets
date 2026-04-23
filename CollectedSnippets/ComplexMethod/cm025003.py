async def test_get_or_create_returns_same_entry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    area_registry: ar.AreaRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Make sure we do not duplicate entries."""
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        sw_version="sw-version",
        name="name",
        manufacturer="manufacturer",
        model="model",
        suggested_area="Game Room",
    )
    entry2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "11:22:33:66:77:88")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
        suggested_area="Game Room",
    )
    entry3 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    game_room_area = area_registry.async_get_area_by_name("Game Room")
    assert game_room_area is not None
    assert len(area_registry.areas) == 1

    assert len(device_registry.devices) == 1
    assert entry.area_id == game_room_area.id
    assert entry.id == entry2.id
    assert entry.id == entry3.id
    assert entry.identifiers == {("bridgeid", "0123")}

    assert entry2.area_id == game_room_area.id

    assert entry3.manufacturer == "manufacturer"
    assert entry3.model == "model"
    assert entry3.name == "name"
    assert entry3.sw_version == "sw-version"
    assert entry3.area_id == game_room_area.id

    await hass.async_block_till_done()

    # Only 2 update events. The third entry did not generate any changes.
    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {"connections": {("mac", "12:34:56:ab:cd:ef")}},
    }