async def test_sync_methods(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test sync method for creating and deleting an issue."""

    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}

    def _create_issue() -> None:
        ir.create_issue(
            hass,
            "fake_integration",
            "sync_issue",
            breaks_in_ha_version="2022.9",
            is_fixable=True,
            is_persistent=False,
            learn_more_url="https://theuselessweb.com",
            severity=ir.IssueSeverity.ERROR,
            translation_key="abc_123",
            translation_placeholders={"abc": "123"},
        )

    await hass.async_add_executor_job(_create_issue)
    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            {
                "breaks_in_ha_version": "2022.9",
                "created": "2022-07-21T08:22:00+00:00",
                "dismissed_version": None,
                "domain": "fake_integration",
                "ignored": False,
                "is_fixable": True,
                "issue_id": "sync_issue",
                "issue_domain": None,
                "learn_more_url": "https://theuselessweb.com",
                "severity": "error",
                "translation_key": "abc_123",
                "translation_placeholders": {"abc": "123"},
            }
        ]
    }

    await hass.async_add_executor_job(
        ir.delete_issue, hass, "fake_integration", "sync_issue"
    )
    await client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": []}