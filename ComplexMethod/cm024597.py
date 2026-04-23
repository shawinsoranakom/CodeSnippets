async def test_missing_backup_no_shares(
    hass: HomeAssistant,
    setup_dsm_with_filestation: MagicMock,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the missing backup location setup repair flow errors out."""
    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    # get repair issues
    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1

    # start repair flow
    data = await start_repair_fix_flow(client, DOMAIN, "missing_backup_setup_my_serial")

    flow_id = data["flow_id"]
    assert data["description_placeholders"] == {
        "docs_url": "https://www.home-assistant.io/integrations/synology_dsm/#backup-location"
    }
    assert data["step_id"] == "init"
    assert data["menu_options"] == ["confirm", "ignore"]

    # inject error
    setup_dsm_with_filestation.file.get_shared_folders.return_value = []

    # select to confirm the flow
    data = await process_repair_fix_flow(
        client, flow_id, json={"next_step_id": "confirm"}
    )
    assert data["type"] == "abort"
    assert data["reason"] == "no_shares"