async def test_cury_switch_availability(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test availability of switch entities for cury component."""
    slots = {
        "left": {
            "intensity": 70,
            "on": True,
            "boost": None,
            "vial": {"level": 27, "name": "Forest Dream"},
        },
        "right": {
            "intensity": 70,
            "on": False,
            "boost": None,
            "vial": {"level": 84, "name": "Velvet Rose"},
        },
    }
    status = {"cury:0": {"id": 0, "slots": slots}}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    await init_integration(hass, 3)

    entity_id = f"{SWITCH_DOMAIN}.test_name_left_slot"

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    slots["left"]["vial"]["level"] = -1
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cury:0", "slots", slots)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE

    slots["left"].pop("vial")
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cury:0", "slots", slots)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE

    slots["left"] = None
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cury:0", "slots", slots)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE

    slots["left"] = {
        "intensity": 70,
        "on": True,
        "boost": None,
        "vial": {"level": 27, "name": "Forest Dream"},
    }
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cury:0", "slots", slots)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON