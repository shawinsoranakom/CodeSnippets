async def test_rpc_device_virtual_text(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
) -> None:
    """Test a virtual text for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["text:203"] = {
        "name": name,
        "meta": {"ui": {"view": "field"}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["text:203"] = {"value": "lorem ipsum"}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == "lorem ipsum"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-text:203-text_generic"

    monkeypatch.setitem(mock_rpc_device.status["text:203"], "value", "dolor sit amet")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "dolor sit amet"

    monkeypatch.setitem(mock_rpc_device.status["text:203"], "value", "sed do eiusmod")
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: "sed do eiusmod"},
        blocking=True,
    )
    mock_rpc_device.mock_update()
    mock_rpc_device.text_set.assert_called_once_with(203, "sed do eiusmod")

    assert (state := hass.states.get(entity_id))
    assert state.state == "sed do eiusmod"