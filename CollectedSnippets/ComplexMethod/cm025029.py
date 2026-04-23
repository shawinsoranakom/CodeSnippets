async def test_suggested_area_deprecation(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    area_registry: ar.AreaRegistry,
    mock_config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Make sure we do not duplicate entries."""
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

    game_room_area = area_registry.async_get_area_by_name("Game Room")
    assert game_room_area is not None
    assert len(area_registry.areas) == 1

    assert len(device_registry.devices) == 1
    assert entry.area_id == game_room_area.id
    assert entry.suggested_area == "Game Room"

    assert (
        "The deprecated function suggested_area was called. It will be removed in "
        "HA Core 2026.9. Use code which ignores suggested_area instead"
    ) in caplog.text

    device_registry.async_update_device(entry.id, suggested_area="TV Room")

    assert (
        "Detected code that passes a suggested_area to device_registry.async_update "
        "device. This will stop working in Home Assistant 2026.9.0, please report "
        "this issue"
    ) in caplog.text