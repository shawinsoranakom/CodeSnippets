async def test_numbers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_wled: MagicMock,
    entity_id: str,
    value: int,
    called_arg: str,
) -> None:
    """Test the creation and values of the WLED numbers."""
    assert (state := hass.states.get(entity_id))
    assert state == snapshot

    assert (entity_entry := entity_registry.async_get(state.entity_id))
    assert entity_entry == snapshot

    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert device_entry == snapshot

    # Test a regular state change service call
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )

    assert mock_wled.segment.call_count == 1
    mock_wled.segment.assert_called_with(segment_id=1, **{called_arg: value})

    # Test with WLED error
    mock_wled.segment.side_effect = WLEDError
    with pytest.raises(HomeAssistantError, match="Invalid response from WLED API"):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
            blocking=True,
        )
    assert mock_wled.segment.call_count == 2

    # Ensure the entity is still available
    assert (state := hass.states.get(entity_id))
    assert state.state != STATE_UNAVAILABLE

    # Test when a connection error occurs
    mock_wled.segment.side_effect = WLEDConnectionError
    with pytest.raises(HomeAssistantError, match="Error communicating with WLED API"):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
            blocking=True,
        )
    assert mock_wled.segment.call_count == 3

    # Ensure the entity became unavailable after the connection error
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE