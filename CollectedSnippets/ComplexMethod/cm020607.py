async def test_main_services(
    hass: HomeAssistant,
    remote_encrypted_websocket: Mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test for turn_off."""
    await setup_samsungtv_entry(hass, ENTRYDATA_ENCRYPTED_WEBSOCKET)

    remote_encrypted_websocket.send_commands.reset_mock()

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    # key called
    assert remote_encrypted_websocket.send_commands.call_count == 1
    commands = remote_encrypted_websocket.send_commands.call_args_list[0].args[0]
    assert len(commands) == 2
    assert isinstance(command := commands[0], SamsungTVEncryptedCommand)
    assert command.body["param3"] == "KEY_POWEROFF"
    assert isinstance(command := commands[1], SamsungTVEncryptedCommand)
    assert command.body["param3"] == "KEY_POWER"

    # commands not sent : power off in progress
    remote_encrypted_websocket.send_commands.reset_mock()
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["dash"]},
        blocking=True,
    )
    assert "TV is powering off, not sending keys: ['dash']" in caplog.text
    remote_encrypted_websocket.send_commands.assert_not_called()