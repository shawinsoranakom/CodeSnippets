async def test_fix_issue_aborted(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test we can fix an issue."""
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, DOMAIN, {})

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await create_issues(
        hass,
        ws_client,
        issues=[
            {
                **DEFAULT_ISSUES[0],
                "domain": "fake_integration",
                "issue_id": "abort_issue1",
            }
        ],
    )

    await ws_client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1

    first_issue = msg["result"]["issues"][0]

    assert first_issue["domain"] == "fake_integration"
    assert first_issue["issue_id"] == "abort_issue1"

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "fake_integration", "issue_id": "abort_issue1"},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "abort",
        "flow_id": flow_id,
        "handler": "fake_integration",
        "reason": "not_given",
        "description_placeholders": None,
    }

    await ws_client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    assert msg["result"]["issues"][0] == first_issue