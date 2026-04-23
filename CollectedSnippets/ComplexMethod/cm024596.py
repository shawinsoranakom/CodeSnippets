async def test_missing_backup_success(
    hass: HomeAssistant,
    setup_dsm_with_filestation: MagicMock,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the missing backup location setup repair flow is fully processed by the user."""
    ws_client = await hass_ws_client(hass)
    client = await hass_client()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.options == {"backup_path": None, "backup_share": None}

    # get repair issues
    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    issue = msg["result"]["issues"][0]
    assert not issue["ignored"]

    # start repair flow
    data = await start_repair_fix_flow(client, DOMAIN, "missing_backup_setup_my_serial")

    flow_id = data["flow_id"]
    assert data["description_placeholders"] == {
        "docs_url": "https://www.home-assistant.io/integrations/synology_dsm/#backup-location"
    }
    assert data["step_id"] == "init"
    assert data["menu_options"] == ["confirm", "ignore"]

    # seelct to confirm the flow
    data = await process_repair_fix_flow(
        client, flow_id, json={"next_step_id": "confirm"}
    )
    assert data["step_id"] == "confirm"
    assert data["type"] == "form"

    # fill out the form and submit
    data = await process_repair_fix_flow(
        client,
        flow_id,
        json={"backup_share": "/ha_backup", "backup_path": "backup_ha_dev"},
    )
    assert data["type"] == "create_entry"
    assert entry.options == {
        "backup_path": "backup_ha_dev",
        "backup_share": "/ha_backup",
    }