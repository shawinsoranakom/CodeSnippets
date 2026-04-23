async def test_outbound_websocket_incorrectly_enabled_issue(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_rpc_device: Mock,
    issue_registry: ir.IssueRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test repair issues handling for the outbound WebSocket incorrectly enabled."""
    ws_url = "ws://10.10.10.10:8123/api/shelly/ws"
    monkeypatch.setitem(
        mock_rpc_device.config, "ws", {"enable": True, "server": ws_url}
    )

    issue_id = OUTBOUND_WEBSOCKET_INCORRECTLY_ENABLED_ISSUE_ID.format(unique=MOCK_MAC)
    assert await async_setup_component(hass, "repairs", {})
    await hass.async_block_till_done()
    await init_integration(hass, 2)

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    assert result["step_id"] == "confirm"

    result = await process_repair_fix_flow(client, flow_id)
    assert result["type"] == "create_entry"
    assert mock_rpc_device.ws_setconfig.call_count == 1
    assert mock_rpc_device.ws_setconfig.call_args[0] == (False, ws_url)
    assert mock_rpc_device.trigger_reboot.call_count == 1

    # Assert the issue is no longer present
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 0