async def test_rpc_cover_tilt(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test RPC cover that supports tilt."""
    entity_id = "cover.test_name_test_cover_0"

    config = deepcopy(mock_rpc_device.config)
    config["cover:0"]["slat"] = {"enable": True}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["cover:0"]["slat_pos"] = 0
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-cover:0"

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_TILT_POSITION: 50},
        blocking=True,
    )
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 50)
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_set_position.assert_called_once_with(0, slat_pos=50)
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    mock_rpc_device.cover_set_position.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 100)
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_set_position.assert_called_once_with(0, slat_pos=100)
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    mock_rpc_device.cover_set_position.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 10)
    mock_rpc_device.mock_update()

    mock_rpc_device.cover_stop.assert_called_once_with(0)
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 10