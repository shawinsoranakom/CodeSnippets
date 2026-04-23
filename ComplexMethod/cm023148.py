async def test_backup_nvm(
    hass: HomeAssistant,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the backup NVM websocket command."""
    ws_client = await hass_ws_client(hass)

    # Set up mocks for the controller events
    controller = client.driver.controller

    # Test subscription and events
    with patch.object(
        controller, "async_backup_nvm_raw_base64", return_value="test"
    ) as mock_backup:
        # Send the subscription request
        await ws_client.send_json_auto_id(
            {
                "type": "zwave_js/backup_nvm",
                "entry_id": integration.entry_id,
            }
        )

        # Verify the finished event with data first
        msg = await ws_client.receive_json()
        assert msg["type"] == "event"
        assert msg["event"]["event"] == "finished"
        assert msg["event"]["data"] == "test"

        # Verify subscription success
        msg = await ws_client.receive_json()
        assert msg["type"] == "result"
        assert msg["success"] is True

        # Simulate progress events
        event = Event(
            "nvm backup progress",
            {
                "source": "controller",
                "event": "nvm backup progress",
                "bytesRead": 25,
                "total": 100,
            },
        )
        controller.receive_event(event)
        msg = await ws_client.receive_json()
        assert msg["event"]["event"] == "nvm backup progress"
        assert msg["event"]["bytesRead"] == 25
        assert msg["event"]["total"] == 100

        event = Event(
            "nvm backup progress",
            {
                "source": "controller",
                "event": "nvm backup progress",
                "bytesRead": 50,
                "total": 100,
            },
        )
        controller.receive_event(event)
        msg = await ws_client.receive_json()
        assert msg["event"]["event"] == "nvm backup progress"
        assert msg["event"]["bytesRead"] == 50
        assert msg["event"]["total"] == 100

        # Wait for the backup to complete
        await hass.async_block_till_done()

        # Verify the backup was called
        assert mock_backup.called

    # Test backup failure
    with patch.object(
        controller,
        "async_backup_nvm_raw_base64",
        side_effect=FailedCommand("failed_command", "Backup failed"),
    ):
        # Send the subscription request
        await ws_client.send_json_auto_id(
            {
                "type": "zwave_js/backup_nvm",
                "entry_id": integration.entry_id,
            }
        )

        # Verify error response
        msg = await ws_client.receive_json()
        assert not msg["success"]
        assert msg["error"]["code"] == "Backup failed"

    # Test config entry not found
    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/backup_nvm",
            "entry_id": "invalid_entry_id",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"

    # Test config entry not loaded
    await hass.config_entries.async_unload(integration.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/backup_nvm",
            "entry_id": integration.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["error"]["code"] == "not_loaded"