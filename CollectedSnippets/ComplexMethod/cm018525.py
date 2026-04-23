async def test_coiot_disabled_or_wrong_peer_issue(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_block_device: Mock,
    issue_registry: ir.IssueRegistry,
    monkeypatch: pytest.MonkeyPatch,
    coiot: dict[str, Any],
) -> None:
    """Test repair issues handling wrong or disabled CoIoT configuration."""
    monkeypatch.setitem(mock_block_device.settings, "coiot", coiot)
    issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
    assert await async_setup_component(hass, "repairs", {})
    await hass.async_block_till_done()
    await init_integration(hass, 1)
    await mock_block_device_push_update_failure(hass, mock_block_device)

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    assert result["step_id"] == "init"
    assert result["type"] == "menu"

    result = await process_repair_fix_flow(client, flow_id, {"next_step_id": "confirm"})

    assert result["type"] == "create_entry"
    assert mock_block_device.configure_coiot_protocol.call_count == 1

    # Assert the issue is no longer present
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 0