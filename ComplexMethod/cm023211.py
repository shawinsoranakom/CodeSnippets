async def test_invalid_issue(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    integration,
) -> None:
    """Test the invalid issue."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "invalid_issue_id",
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="invalid_issue",
    )

    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)
    http_client = await hass_client()

    # Assert the issue is present
    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    issue = msg["result"]["issues"][0]
    assert issue["issue_id"] == "invalid_issue_id"

    data = await start_repair_fix_flow(http_client, DOMAIN, "invalid_issue_id")

    flow_id = data["flow_id"]
    assert data["step_id"] == "confirm"

    # Apply fix
    data = await process_repair_fix_flow(http_client, flow_id)

    assert data["type"] == "create_entry"

    await hass.async_block_till_done()

    # Assert the issue is resolved
    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 0