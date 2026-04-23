async def test_send_command(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
) -> None:
    """Test the send command service."""
    mock_controller = MagicMock()
    mock_homeworks.return_value = mock_controller

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_controller._send.reset_mock()
    await hass.services.async_call(
        DOMAIN,
        "send_command",
        {"controller_id": "main_controller", "command": "KBP, [02:08:02:01], 1"},
        blocking=True,
    )
    assert len(mock_controller._send.mock_calls) == 1
    assert mock_controller._send.mock_calls[0][1] == ("KBP, [02:08:02:01], 1",)

    mock_controller._send.reset_mock()
    await hass.services.async_call(
        DOMAIN,
        "send_command",
        {
            "controller_id": "main_controller",
            "command": [
                "KBP, [02:08:02:01], 1",
                "KBH, [02:08:02:01], 1",
                "KBR, [02:08:02:01], 1",
            ],
        },
        blocking=True,
    )
    assert len(mock_controller._send.mock_calls) == 3
    assert mock_controller._send.mock_calls[0][1] == ("KBP, [02:08:02:01], 1",)
    assert mock_controller._send.mock_calls[1][1] == ("KBH, [02:08:02:01], 1",)
    assert mock_controller._send.mock_calls[2][1] == ("KBR, [02:08:02:01], 1",)

    mock_controller._send.reset_mock()
    await hass.services.async_call(
        DOMAIN,
        "send_command",
        {
            "controller_id": "main_controller",
            "command": [
                "KBP, [02:08:02:01], 1",
                "delay 50",
                "KBH, [02:08:02:01], 1",
                "dElAy 100",
                "KBR, [02:08:02:01], 1",
            ],
        },
        blocking=True,
    )
    assert len(mock_controller._send.mock_calls) == 3
    assert mock_controller._send.mock_calls[0][1] == ("KBP, [02:08:02:01], 1",)
    assert mock_controller._send.mock_calls[1][1] == ("KBH, [02:08:02:01], 1",)
    assert mock_controller._send.mock_calls[2][1] == ("KBR, [02:08:02:01], 1",)

    mock_controller._send.reset_mock()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "send_command",
            {"controller_id": "unknown_controller", "command": "KBP, [02:08:02:01], 1"},
            blocking=True,
        )
    assert len(mock_controller._send.mock_calls) == 0