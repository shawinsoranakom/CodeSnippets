async def test_migrate_unique_id_non_integer_ids(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the migrate unique id flow with non-integer unique IDs."""
    old_unique_id = "non_numeric_id"
    new_unique_id = "also_invalid"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://test.org",
        },
        unique_id=old_unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    # Manually create the repair issue with non-integer unique IDs
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"migrate_unique_id.{config_entry.entry_id}",
        data={
            "config_entry_id": config_entry.entry_id,
            "config_entry_title": "Z-Wave JS",
            "controller_model": "ZW090",
            "new_unique_id": new_unique_id,
            "old_unique_id": old_unique_id,
        },
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="migrate_unique_id",
    )

    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)
    http_client = await hass_client()

    # Assert the issue is present
    await ws_client.send_json_auto_id({"type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    issue = msg["result"]["issues"][0]
    issue_id = issue["issue_id"]
    assert issue_id == f"migrate_unique_id.{config_entry.entry_id}"

    data = await start_repair_fix_flow(http_client, DOMAIN, issue_id)

    flow_id = data["flow_id"]
    assert data["step_id"] == "confirm"
    # The non-integer IDs should be displayed as-is
    assert data["description_placeholders"] == {
        "config_entry_title": "Z-Wave JS",
        "controller_model": "ZW090",
        "new_unique_id": new_unique_id,
        "old_unique_id": old_unique_id,
    }

    # Apply fix
    data = await process_repair_fix_flow(http_client, flow_id)

    assert data["type"] == "create_entry"
    assert config_entry.unique_id == new_unique_id

    await ws_client.send_json_auto_id({"type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 0