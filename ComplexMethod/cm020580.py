async def test_websocket_unsupported_remote_control(
    hass: HomeAssistant,
    remote_websocket: Mock,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test for turn_off."""
    entry = await setup_samsungtv_entry(hass, MOCK_ENTRY_WS)

    assert entry.data[CONF_METHOD] == METHOD_WEBSOCKET
    assert entry.data[CONF_PORT] == 8001

    remote_websocket.send_commands.reset_mock()

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID}, True
    )
    remote_websocket.raise_mock_ws_event_callback(
        "ms.error",
        {
            "event": "ms.error",
            "data": {"message": "unrecognized method value : ms.remote.control"},
        },
    )

    # key called
    assert remote_websocket.send_commands.call_count == 1
    commands = remote_websocket.send_commands.call_args_list[0].args[0]
    assert len(commands) == 1
    assert isinstance(commands[0], SendRemoteKey)
    assert commands[0].params["DataOfCmd"] == "KEY_POWER"

    # error logged
    assert (
        "Your TV seems to be unsupported by SamsungTVWSBridge and needs a PIN: "
        "'unrecognized method value : ms.remote.control'" in caplog.text
    )

    # Wait config_entry reload
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=ENTRY_RELOAD_COOLDOWN))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # ensure reauth triggered, and method/port updated
    assert [
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["context"]["source"] == "reauth"
    ]
    assert entry.data[CONF_METHOD] == METHOD_ENCRYPTED_WEBSOCKET
    assert entry.data[CONF_PORT] == ENCRYPTED_WEBSOCKET_PORT
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE