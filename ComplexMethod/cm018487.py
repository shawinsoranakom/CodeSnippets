async def test_block_channel_with_name(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
) -> None:
    """Test block channel with name."""
    monkeypatch.setitem(
        mock_block_device.settings["relays"][0], "name", "Kitchen light"
    )

    await init_integration(hass, 1)

    # channel 1 sub-device; num_outputs is 2 so the name of the channel should be used
    entity_id = "switch.kitchen_light"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Kitchen light"

    # main device
    entity_id = "update.test_name_firmware"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name"