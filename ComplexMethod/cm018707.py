async def test_get_issue_data(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we can get issue data."""

    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "data": None,
            "domain": "test",
            "is_fixable": True,
            "issue_id": "issue_1",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com",
            "severity": "error",
            "translation_key": "abc_123",
            "translation_placeholders": {"abc": "123"},
        },
        {
            "breaks_in_ha_version": "2022.8",
            "data": {"key": "value"},
            "domain": "test",
            "is_fixable": False,
            "issue_id": "issue_2",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com/abc",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "456"},
        },
    ]

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            data=issue["data"],
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "issue_1"}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"issue_data": None}

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "issue_2"}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"issue_data": {"key": "value"}}

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "unknown"}
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "unknown_issue",
        "message": "Issue 'unknown' not found",
    }