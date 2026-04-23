async def test_rpc_water_valve(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device Shelly Water Valve."""
    config = deepcopy(mock_rpc_device.config)
    config["number:200"] = {
        "name": "Position",
        "min": 0,
        "max": 100,
        "meta": {"ui": {"step": 10, "view": "slider", "unit": "%"}},
        "role": "position",
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["number:200"] = {"value": 0}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3, model=MODEL_FRANKEVER_WATER_VALVE)
    entity_id = "valve.test_name"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-number:200-water_valve"

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.CLOSED

    # Open valve
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_OPEN_VALVE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.number_set.assert_called_once_with(200, 100)

    status["number:200"] = {"value": 100}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.OPEN

    # Close valve
    mock_rpc_device.number_set.reset_mock()
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_CLOSE_VALVE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.number_set.assert_called_once_with(200, 0)

    status["number:200"] = {"value": 0}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.CLOSED

    # Set valve position to 50%
    mock_rpc_device.number_set.reset_mock()
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_SET_VALVE_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
        blocking=True,
    )

    mock_rpc_device.number_set.assert_called_once_with(200, 50)

    status["number:200"] = {"value": 50}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 50