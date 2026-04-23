async def test_block_device_support_transition(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    model: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device supports transition."""
    # num_outputs is 2, device name and channel name is used
    entity_id = "light.test_name_channel_1"
    monkeypatch.setitem(
        mock_block_device.settings, "fw", "20220809-122808/v1.12-g99f7e0b"
    )
    monkeypatch.setattr(
        mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
    )
    await init_integration(hass, 1, model=model)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & LightEntityFeature.TRANSITION

    # Turn on, TRANSITION = 4
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 4},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", transition=4000
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    # Turn off, TRANSITION = 6, limit to 5000ms
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 6},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="off", transition=5000
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-light_1"