async def test_block_device_services(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test block device cover services."""
    entity_id = "cover.test_name"
    monkeypatch.setitem(mock_block_device.settings, "mode", "roller")
    await init_integration(hass, 1)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.OPENING

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.CLOSING

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.CLOSED

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-roller_0"