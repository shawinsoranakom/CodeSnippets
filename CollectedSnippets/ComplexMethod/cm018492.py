async def test_rpc_presencezone_component(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test RPC binary sensor entity for presencezone component."""
    config = deepcopy(mock_rpc_device.config)
    config["presencezone:200"] = {"name": "Main zone", "enable": True}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["presencezone:200"] = {"value": True, "num_objects": 3}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    mock_config_entry = await init_integration(hass, 4)

    entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_main_zone_occupancy"

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-presencezone:200-presencezone_state"

    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "presencezone:200", "value", False
    )
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    config = deepcopy(mock_rpc_device.config)
    config["presencezone:200"] = {"enable": False}
    monkeypatch.setattr(mock_rpc_device, "config", config)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE