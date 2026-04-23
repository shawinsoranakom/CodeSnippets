async def test_unsupported_firmware_issue_update_not_available(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test repair issues handling when firmware update is not available."""
    issue_id = BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=MOCK_MAC)
    assert await async_setup_component(hass, "repairs", {})
    await hass.async_block_till_done()
    await init_integration(
        hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
    )

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    assert result["step_id"] == "confirm"

    monkeypatch.setitem(mock_rpc_device.status, "sys", {"available_updates": {}})
    result = await process_repair_fix_flow(client, flow_id)
    assert result["type"] == "abort"
    assert result["reason"] == "update_not_available"
    assert mock_rpc_device.trigger_ota_update.call_count == 0

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1