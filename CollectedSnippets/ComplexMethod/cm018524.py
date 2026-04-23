async def test_other_fixable_issues(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_rpc_device: Mock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test fixing another issue."""
    issue_id = "other_issue"
    assert await async_setup_component(hass, "repairs", {})
    await hass.async_block_till_done()
    entry = await init_integration(hass, 2)
    assert mock_rpc_device.initialized is True

    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={"entry_id": entry.entry_id},
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="other_issue",
    )

    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    assert result["step_id"] == "confirm"
    assert result["type"] == "form"

    result = await process_repair_fix_flow(client, flow_id)
    assert result["type"] == "create_entry"