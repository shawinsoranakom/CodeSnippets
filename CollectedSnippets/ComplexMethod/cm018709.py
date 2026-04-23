async def test_ignore_issue(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test ignoring issues."""
    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}

    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "domain": "test",
            "is_fixable": True,
            "issue_id": "issue_1",
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

    # Ignore a non-existing issue
    with pytest.raises(KeyError):
        ir.async_ignore_issue(hass, issues[0]["domain"], "no_such_issue", True)

    await client.send_json({"id": 3, "type": "repairs/list_issues"})
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

    # Ignore an existing issue
    ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], True)

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=ha_version,
                ignored=True,
                issue_domain=None,
            )
            for issue in issues
        ]
    }

    # Ignore the same issue again
    ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], True)

    await client.send_json({"id": 5, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=ha_version,
                ignored=True,
                issue_domain=None,
            )
            for issue in issues
        ]
    }

    # Update an ignored issue
    ir.async_create_issue(
        hass,
        issues[0]["domain"],
        issues[0]["issue_id"],
        breaks_in_ha_version=issues[0]["breaks_in_ha_version"],
        is_fixable=issues[0]["is_fixable"],
        is_persistent=False,
        learn_more_url="blablabla",
        severity=issues[0]["severity"],
        translation_key=issues[0]["translation_key"],
        translation_placeholders=issues[0]["translation_placeholders"],
    )

    await client.send_json({"id": 6, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"]["issues"][0] == dict(
        issues[0],
        created="2022-07-19T07:53:05+00:00",
        dismissed_version=ha_version,
        ignored=True,
        learn_more_url="blablabla",
        issue_domain=None,
    )

    # Unignore the same issue
    ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], False)

    await client.send_json({"id": 7, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            dict(
                issue,
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=None,
                ignored=False,
                learn_more_url="blablabla",
                issue_domain=None,
            )
            for issue in issues
        ]
    }