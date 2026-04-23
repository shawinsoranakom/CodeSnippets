async def test_block_number_update(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device number update."""
    entity_id = "number.test_name_valve_position"
    monkeypatch.setitem(
        mock_block_device.settings,
        "sleep_mode",
        {"period": 60, "unit": "m"},
    )
    await init_integration(hass, 1, sleep_period=3600)

    assert hass.states.get(entity_id) is None

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == "50"

    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valvePos", 30)
    mock_block_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "30"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-device_0-valvePos"