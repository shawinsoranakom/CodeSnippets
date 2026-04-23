async def test_color_palette_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_wled: MagicMock,
    entity_id: str,
    option: str,
    method: str,
    called_with: dict[str, int | str],
) -> None:
    """Test the behavior of the WLED selects."""
    method_mock = getattr(mock_wled, method)

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        blocking=True,
    )
    assert method_mock.call_count == 1
    method_mock.assert_called_with(**called_with)

    # Test invalid response, not becoming unavailable
    method_mock.side_effect = WLEDError
    with pytest.raises(HomeAssistantError, match="Invalid response from WLED API"):
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
            blocking=True,
        )

    assert (state := hass.states.get(entity_id))
    assert state.state != STATE_UNAVAILABLE
    assert method_mock.call_count == 2
    method_mock.assert_called_with(**called_with)

    # Test connection error, leading to becoming unavailable
    method_mock.side_effect = WLEDConnectionError
    with pytest.raises(HomeAssistantError, match="Error communicating with WLED API"):
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: state.entity_id, ATTR_OPTION: option},
            blocking=True,
        )

    assert (state := hass.states.get(state.entity_id))
    assert state.state == STATE_UNAVAILABLE
    assert method_mock.call_count == 3
    method_mock.assert_called_with(**called_with)