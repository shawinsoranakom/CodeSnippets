async def test_reauth_on_403(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_onedrive_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test we re-authenticate on 403."""

    mock_onedrive_client.list_drive_items.side_effect = AuthenticationError(
        403, "Auth failed"
    )
    backup_id = BACKUP_METADATA["backup_id"]
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    assert response["success"]
    assert response["result"]["agent_errors"] == {
        f"{DOMAIN}.{mock_config_entry.unique_id}": "Authentication error"
    }

    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id