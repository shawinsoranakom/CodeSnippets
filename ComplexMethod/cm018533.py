async def test_block_device_relay_app_type_light(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device relay in app type set to light mode."""
    entity_id = "light.test_name_channel_1"
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "red")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "green")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "blue")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "mode")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "gain")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "brightness")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "effect")
    monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "colorTemp")
    monkeypatch.setitem(
        mock_block_device.settings["relays"][RELAY_BLOCK_ID], "appliance_type", "light"
    )
    monkeypatch.setattr(
        mock_block_device.blocks[RELAY_BLOCK_ID], "description", "relay_1"
    )
    await init_integration(hass, 1)

    assert hass.states.get("switch.test_name_channel_1") is None

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Turn off
    mock_block_device.blocks[RELAY_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_block_device.blocks[RELAY_BLOCK_ID].set_state.assert_called_once_with(
        turn="off"
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Turn on
    mock_block_device.blocks[RELAY_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_block_device.blocks[RELAY_BLOCK_ID].set_state.assert_called_once_with(
        turn="on"
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-relay_1"