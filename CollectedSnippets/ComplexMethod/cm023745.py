async def test_agents_list_backups_reauth(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_dropbox_client: Mock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauthentication is triggered on auth error."""

    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxAuthException("auth failed")
    )

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    assert response["success"]
    assert response["result"]["backups"] == []
    assert response["result"]["agent_errors"] == {TEST_AGENT_ID: "Authentication error"}

    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id