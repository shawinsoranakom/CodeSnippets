async def test_rpc_cury_mode_select(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Cury Mode select entity."""
    entity_id = f"{SELECT_DOMAIN}.test_name_mode"
    status = {"cury:0": {"id": 0, "mode": "hall"}}
    monkeypatch.setattr(mock_rpc_device, "status", status)
    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == "hall"
    assert state.attributes.get(ATTR_OPTIONS) == [
        "hall",
        "bedroom",
        "living_room",
        "lavatory_room",
        "none",
        "reception",
        "workplace",
    ]
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Test name Mode"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-cury:0-cury_mode"
    assert entry.translation_key == "cury_mode"

    monkeypatch.setitem(mock_rpc_device.status["cury:0"], "mode", "living_room")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "living_room"

    monkeypatch.setitem(mock_rpc_device.status["cury:0"], "mode", "reception")
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "reception"},
        blocking=True,
    )

    mock_rpc_device.cury_set_mode.assert_called_once_with(0, "reception")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "reception"

    monkeypatch.setitem(mock_rpc_device.status["cury:0"], "mode", None)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "none"