async def test_rpc_device_virtual_enum(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
    value: str | None,
    expected_state: str,
) -> None:
    """Test a virtual enum for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["enum:203"] = {
        "name": name,
        "options": ["option 1", "option 2", "option 3"],
        "meta": {
            "ui": {
                "view": "dropdown",
                "titles": {"option 1": "Title 1", "option 2": None},
            }
        },
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["enum:203"] = {"value": value}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == expected_state
    assert state.attributes.get(ATTR_OPTIONS) == [
        "Title 1",
        "option 2",
        "option 3",
    ]

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-enum:203-enum_generic"

    monkeypatch.setitem(mock_rpc_device.status["enum:203"], "value", "option 2")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "option 2"

    monkeypatch.setitem(mock_rpc_device.status["enum:203"], "value", "option 1")
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "Title 1"},
        blocking=True,
    )
    # 'Title 1' corresponds to 'option 1'
    mock_rpc_device.enum_set.assert_called_once_with(203, "option 1")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "Title 1"