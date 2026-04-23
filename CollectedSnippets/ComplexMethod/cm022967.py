async def test_switch_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_wled: MagicMock,
    entity_id: str,
    method: str,
    called_with_on: dict[str, bool | int],
    called_with_off: dict[str, bool | int],
) -> None:
    """Test the behavior of the switch."""
    # Test on/off services
    method_mock = getattr(mock_wled, method)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert method_mock.call_count == 1
    method_mock.assert_called_with(**called_with_on)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert method_mock.call_count == 2
    method_mock.assert_called_with(**called_with_off)

    # Test invalid response, not becoming unavailable
    method_mock.side_effect = WLEDError
    with pytest.raises(HomeAssistantError, match="Invalid response from WLED API"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert method_mock.call_count == 3
    assert (state := hass.states.get(entity_id))
    assert state.state != STATE_UNAVAILABLE

    # Test connection error, leading to becoming unavailable
    method_mock.side_effect = WLEDConnectionError
    with pytest.raises(HomeAssistantError, match="Error communicating with WLED API"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: state.entity_id},
            blocking=True,
        )

    assert method_mock.call_count == 4
    assert (state := hass.states.get(state.entity_id))
    assert state.state == STATE_UNAVAILABLE