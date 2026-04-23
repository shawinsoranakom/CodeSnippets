async def test_rpc_device_services(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test RPC device cover services."""
    entity_id = "cover.test_name_test_cover_0"
    await init_integration(hass, 2)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
        blocking=True,
    )

    mock_rpc_device.cover_set_position.assert_called_once_with(0, pos=50)
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "cover:0", "state", "opening"
    )
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_open.assert_called_once_with(0)
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.OPENING

    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "cover:0", "state", "closing"
    )
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_close.assert_called_once_with(0)
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.CLOSING

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cover:0", "state", "closed")
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_stop.assert_called_once_with(0)
    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.CLOSED

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-cover:0"