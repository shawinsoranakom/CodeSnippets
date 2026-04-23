async def test_select_set_reauth_error(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test select setting with authentication error."""
    config = deepcopy(mock_rpc_device.config)
    config["enum:203"] = {
        "name": None,
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
    status["enum:203"] = {"value": "option 1"}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    entry = await init_integration(hass, 3)

    mock_rpc_device.enum_set.side_effect = InvalidAuthError

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"{SELECT_DOMAIN}.test_name_enum_203",
            ATTR_OPTION: "option 2",
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