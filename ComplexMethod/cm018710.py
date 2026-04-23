async def test_delete_issue(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we can delete an issue."""
    freezer.move_to("2022-07-19 07:53:05")
    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "domain": "fake_integration",
            "issue_id": "issue_1",
            "is_fixable": True,
            "learn_more_url": "https://theuselessweb.com",
            "severity": "error",
            "translation_key": "abc_123",
            "translation_placeholders": {"abc": "123"},
        },
    ]

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=None,
                ignored=False,
                issue_domain=None,
            )
            for issue in issues
        ]
    }

    # Delete a non-existing issue
    ir.async_delete_issue(hass, issues[0]["domain"], "no_such_issue")

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=None,
                ignored=False,
                issue_domain=None,
            )
            for issue in issues
        ]
    }

    # Delete an existing issue
    ir.async_delete_issue(hass, issues[0]["domain"], issues[0]["issue_id"])

    await client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}

    # Delete the same issue again
    ir.async_delete_issue(hass, issues[0]["domain"], issues[0]["issue_id"])

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}

    # Create the same issues again created timestamp should change
    freezer.move_to("2022-07-19 08:53:05")

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await client.send_json({"id": 5, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T08:53:05+00:00",
                dismissed_version=None,
                ignored=False,
                issue_domain=None,
            )
            for issue in issues
        ]
    }