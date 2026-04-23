async def test_bad_date_holiday(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test fixing bad province selecting none."""
    assert await async_setup_component(hass, "repairs", {})
    entry = await init_integration(hass, TEST_CONFIG_REMOVE_DATE)

    state = hass.states.get("binary_sensor.workday_sensor")
    assert state

    issues = issue_registry.issues.keys()
    for issue in issues:
        if issue[0] == DOMAIN:
            assert issue[1].startswith("bad_date")

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert len(msg["result"]["issues"]) > 0
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_05":
            issue = i
    assert issue is not None

    data = await start_repair_fix_flow(client, DOMAIN, "bad_date_holiday-1-2024_02_05")

    flow_id = data["flow_id"]
    assert data["description_placeholders"] == {
        CONF_COUNTRY: "US",
        CONF_REMOVE_HOLIDAYS: "2024-02-05",
        "title": entry.title,
    }
    assert data["step_id"] == "fix_remove_holiday"

    data = await process_repair_fix_flow(
        client, flow_id, json={"remove_holidays": ["2024-02-06"]}
    )

    assert data["type"] == "create_entry"
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    assert state

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_05":
            issue = i
    assert not issue
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_06":
            issue = i
    assert issue