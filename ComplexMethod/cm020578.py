async def test_turn_off_websocket_frame(
    hass: HomeAssistant, remote_websocket: Mock, rest_api: Mock
) -> None:
    """Test for turn_off."""
    rest_api.rest_device_info.return_value = await async_load_json_object_fixture(
        hass, "device_info_UE43LS003.json", DOMAIN
    )
    with patch(
        "homeassistant.components.samsungtv.bridge.Remote",
        side_effect=[OSError("Boom"), DEFAULT_MOCK],
    ):
        await setup_samsungtv_entry(hass, MOCK_CONFIGWS)

    remote_websocket.send_commands.reset_mock()

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID}, True
    )
    # key called
    assert remote_websocket.send_commands.call_count == 1
    commands = remote_websocket.send_commands.call_args_list[0].args[0]
    assert len(commands) == 3
    assert isinstance(commands[0], SendRemoteKey)
    assert commands[0].params["Cmd"] == "Press"
    assert commands[0].params["DataOfCmd"] == "KEY_POWER"
    assert isinstance(commands[1], SamsungTVSleepCommand)
    assert commands[1].delay == 3
    assert isinstance(commands[2], SendRemoteKey)
    assert commands[2].params["Cmd"] == "Release"
    assert commands[2].params["DataOfCmd"] == "KEY_POWER"