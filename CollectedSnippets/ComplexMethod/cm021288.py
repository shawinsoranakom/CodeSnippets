async def test_send_command_event_propagation(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test event propagation for send_command service."""
    domain = "light"
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        domain: {
            "platform": "rflink",
            "devices": {
                "protocol_0_1": {"name": "test1"},
            },
        },
    }

    # setup mocking rflink module
    _, _, protocol, _ = await mock_rflink(hass, config, domain, monkeypatch)

    # default value = 'off'
    assert hass.states.get(f"{domain}.test1").state == "off"

    await hass.services.async_call(
        "rflink",
        SERVICE_SEND_COMMAND,
        {"device_id": "protocol_0_1", "command": "on"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert protocol.send_command_ack.call_args_list[0][0][0] == "protocol_0_1"
    assert protocol.send_command_ack.call_args_list[0][0][1] == "on"
    assert hass.states.get(f"{domain}.test1").state == "on"

    await hass.services.async_call(
        "rflink",
        SERVICE_SEND_COMMAND,
        {"device_id": "protocol_0_1", "command": "alloff"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert protocol.send_command_ack.call_args_list[1][0][0] == "protocol_0_1"
    assert protocol.send_command_ack.call_args_list[1][0][1] == "alloff"
    assert hass.states.get(f"{domain}.test1").state == "off"