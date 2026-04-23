async def test_rpc_neo_water_valve(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device Shelly NEO Water Valve."""
    config = deepcopy(mock_rpc_device.config)
    config["boolean:200"] = {
        "name": "State",
        "meta": {"ui": {"view": "toggle"}},
        "role": "state",
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["boolean:200"] = {"value": False}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3, model=MODEL_NEO_WATER_VALVE)
    entity_id = "valve.test_name"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-boolean:200-neo_water_valve"

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.CLOSED

    # Open valve
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_OPEN_VALVE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.boolean_set.assert_called_once_with(200, True)

    status["boolean:200"] = {"value": True}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.OPEN

    # Close valve
    mock_rpc_device.boolean_set.reset_mock()
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_CLOSE_VALVE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.boolean_set.assert_called_once_with(200, False)

    status["boolean:200"] = {"value": False}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ValveState.CLOSED