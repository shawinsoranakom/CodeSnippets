async def test_light(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    monkeypatch: pytest.MonkeyPatch,
    device,
    entity_id: str,
    light_id: int,
    device_state: list[DeviceState],
) -> None:
    """Test the light."""
    await init_integration(hass, USERNAME, TOKEN)
    assert mock_bridge

    # Test initial state - light on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Test state change on --> off for light
    monkeypatch.setattr(device, "light", device_state)
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test turning on light
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_light",
    ) as mock_set_light:
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 2
        mock_set_light.assert_called_once_with(DeviceState.ON, light_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON

    # Test turning off light
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_light"
    ) as mock_set_light:
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 4
        mock_set_light.assert_called_once_with(DeviceState.OFF, light_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF