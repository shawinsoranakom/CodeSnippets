async def test_coiot_exception(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_block_device: Mock,
    issue_registry: ir.IssueRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test CoIoT exception handling in fix flow."""
    monkeypatch.setitem(
        mock_block_device.settings,
        "coiot",
        {"enabled": False, "update_period": 15, "peer": "7.7.7.7:5683"},
    )
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

    mock_block_device.configure_coiot_protocol.side_effect = DeviceConnectionError
    result = await process_repair_fix_flow(client, flow_id, {"next_step_id": "confirm"})

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"
    assert mock_block_device.configure_coiot_protocol.call_count == 1

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1