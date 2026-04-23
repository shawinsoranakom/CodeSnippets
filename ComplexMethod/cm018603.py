async def test_text_set_reauth_error(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test text setting with authentication error."""
    config = deepcopy(mock_rpc_device.config)
    config["text:203"] = {
        "name": None,
        "meta": {"ui": {"view": "field"}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["text:203"] = {"value": "lorem ipsum"}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    entry = await init_integration(hass, 3)

    mock_rpc_device.text_set.side_effect = InvalidAuthError

    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"{TEXT_DOMAIN}.test_name_text_203",
            ATTR_VALUE: "new value",
        },
        blocking=True,
    )

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id