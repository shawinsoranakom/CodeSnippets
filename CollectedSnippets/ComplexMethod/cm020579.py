async def test_turn_off_encrypted_websocket(
    hass: HomeAssistant,
    remote_encrypted_websocket: Mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test for turn_off."""
    entry_data = deepcopy(ENTRYDATA_ENCRYPTED_WEBSOCKET)
    entry_data[CONF_MODEL] = "UE48UNKNOWN"
    await setup_samsungtv_entry(hass, entry_data)

    remote_encrypted_websocket.send_commands.reset_mock()

    caplog.clear()
    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID}, True
    )
    # key called
    assert remote_encrypted_websocket.send_commands.call_count == 1
    commands = remote_encrypted_websocket.send_commands.call_args_list[0].args[0]
    assert len(commands) == 2
    assert isinstance(command := commands[0], SamsungTVEncryptedCommand)
    assert command.body["param3"] == "KEY_POWEROFF"
    assert isinstance(command := commands[1], SamsungTVEncryptedCommand)
    assert command.body["param3"] == "KEY_POWER"
    assert "Unknown power_off command for UE48UNKNOWN (10.10.12.34)" in caplog.text

    # commands not sent : power off in progress
    remote_encrypted_websocket.send_commands.reset_mock()
    await hass.services.async_call(
        MP_DOMAIN, SERVICE_VOLUME_UP, {ATTR_ENTITY_ID: ENTITY_ID}, True
    )
    assert "TV is powering off, not sending keys: ['KEY_VOLUP']" in caplog.text
    remote_encrypted_websocket.send_commands.assert_not_called()