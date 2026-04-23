async def test_agents_delete(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_dsm_with_filestation: MagicMock,
) -> None:
    """Test agent delete backup."""
    client = await hass_ws_client(hass)
    backup_id = "abcd12ef"

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": backup_id,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"agent_errors": {}}
    mock: AsyncMock = setup_dsm_with_filestation.file.delete_file
    assert len(mock.mock_calls) == 2
    assert mock.call_args_list[0].kwargs["filename"] == f"{BASE_FILENAME}.tar"
    assert mock.call_args_list[0].kwargs["path"] == "/ha_backup/my_backup_path"
    assert mock.call_args_list[1].kwargs["filename"] == f"{BASE_FILENAME}_meta.json"
    assert mock.call_args_list[1].kwargs["path"] == "/ha_backup/my_backup_path"