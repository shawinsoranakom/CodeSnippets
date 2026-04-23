async def test_websocket_update_preview_feature_backup_scenarios(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    create_backup: bool,
    backup_fails: bool,
    enabled: bool,
    should_call_backup: bool,
    should_succeed: bool,
) -> None:
    """Test various backup scenarios when updating preview features."""
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Mock the backup manager
    mock_backup_manager = AsyncMock()
    if backup_fails:
        mock_backup_manager.async_create_automatic_backup = AsyncMock(
            side_effect=Exception("Backup failed")
        )
    else:
        mock_backup_manager.async_create_automatic_backup = AsyncMock()

    with patch(
        "homeassistant.components.labs.websocket_api.async_get_manager",
        return_value=mock_backup_manager,
    ):
        await client.send_json_auto_id(
            {
                "type": "labs/update",
                "domain": "kitchen_sink",
                "preview_feature": "special_repair",
                "enabled": enabled,
                "create_backup": create_backup,
            }
        )
        msg = await client.receive_json()

    if should_succeed:
        assert msg["success"]
        if should_call_backup:
            mock_backup_manager.async_create_automatic_backup.assert_called_once()
        else:
            mock_backup_manager.async_create_automatic_backup.assert_not_called()
    else:
        assert not msg["success"]
        assert msg["error"]["code"] == "unknown_error"
        assert "backup" in msg["error"]["message"].lower()
        # Verify preview feature was NOT enabled
        assert not async_is_preview_feature_enabled(
            hass, "kitchen_sink", "special_repair"
        )