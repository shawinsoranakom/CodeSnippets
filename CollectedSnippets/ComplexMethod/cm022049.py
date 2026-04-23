async def test_special_repair_preview_feature_toggle(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that special repair issue is created/deleted when preview feature is toggled."""
    # Setup repairs and kitchen_sink first
    assert await async_setup_component(hass, "labs", {})
    assert await async_setup_component(hass, "repairs", {})
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    ws_client = await hass_ws_client(hass)

    # Enable the special repair preview feature
    await ws_client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    # Check issue exists
    issue = issue_registry.async_get_issue(DOMAIN, "kitchen_sink_special_repair_issue")
    assert issue is not None

    # Disable the special repair preview feature
    await ws_client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": False,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    # Check issue is removed
    issue = issue_registry.async_get_issue(DOMAIN, "kitchen_sink_special_repair_issue")
    assert issue is None