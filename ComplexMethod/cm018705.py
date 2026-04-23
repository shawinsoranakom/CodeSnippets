async def test_fix_issue(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    domain,
    step,
    description_placeholders,
) -> None:
    """Test we can fix an issue."""
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, DOMAIN, {})

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    issues = [
        {
            **DEFAULT_ISSUES[0],
            "data": {"blah": "bleh"},
            "domain": domain,
            "issue_id": "issue_2",
        }
    ]
    await create_issues(hass, ws_client, issues=issues)

    url = "/api/repairs/issues/fix"
    resp = await client.post(url, json={"handler": domain, "issue_id": "issue_2"})

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "data_schema": [],
        "description_placeholders": description_placeholders,
        "errors": None,
        "flow_id": ANY,
        "handler": domain,
        "last_step": None,
        "preview": None,
        "step_id": step,
        "type": "form",
    }

    url = f"/api/repairs/issues/fix/{flow_id}"
    # Test we can get the status of the flow
    resp2 = await client.get(url)

    assert resp2.status == HTTPStatus.OK
    data2 = await resp2.json()

    assert data == data2

    resp = await client.post(url)

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "description": None,
        "description_placeholders": None,
        "flow_id": flow_id,
        "handler": domain,
        "type": "create_entry",
    }

    await ws_client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}