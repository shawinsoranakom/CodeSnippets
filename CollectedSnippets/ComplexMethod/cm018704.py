async def test_dismiss_issue(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we can dismiss an issue."""
    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    issues = await create_issues(hass, client)

    await client.send_json(
        {
            "id": 2,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "no_such_issue",
            "ignore": True,
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]

    await client.send_json(
        {
            "id": 3,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "issue_1",
            "ignore": True,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created=ANY,
                dismissed_version=ha_version,
                ignored=True,
                issue_domain=None,
            )
            for issue in issues
        ]
    }

    await client.send_json(
        {
            "id": 5,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "issue_1",
            "ignore": False,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    await client.send_json({"id": 6, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created=ANY,
                dismissed_version=None,
                ignored=False,
                issue_domain=None,
            )
            for issue in issues
        ]
    }