async def test_knx_subscribe_telegrams_command_no_project(
    hass: HomeAssistant, knx: KNXTestKit, hass_ws_client: WebSocketGenerator
) -> None:
    """Test knx/subscribe_telegrams command without project data."""
    await knx.setup_integration(
        {
            SwitchSchema.PLATFORM: {
                CONF_NAME: "test",
                KNX_ADDRESS: "1/2/4",
            }
        }
    )
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "knx/subscribe_telegrams"})
    res = await client.receive_json()
    assert res["success"], res

    # send incoming telegrams
    await knx.receive_read("1/2/3")
    await knx.receive_write("1/3/4", True)
    await knx.receive_write("1/3/4", False)
    await knx.receive_write("1/3/8", (0x34, 0x45))
    # send outgoing telegrams
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.test"}, blocking=True
    )
    await knx.assert_write("1/2/4", 1)
    # receive undecodable data secure telegram
    knx.receive_data_secure_issue("1/2/5")

    # receive events
    res = await client.receive_json()
    assert res["event"]["destination"] == "1/2/3"
    assert res["event"]["payload"] is None
    assert res["event"]["telegramtype"] == "GroupValueRead"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    res = await client.receive_json()
    assert res["event"]["destination"] == "1/3/4"
    assert res["event"]["payload"] == 1
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    res = await client.receive_json()
    assert res["event"]["destination"] == "1/3/4"
    assert res["event"]["payload"] == 0
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    res = await client.receive_json()
    assert res["event"]["destination"] == "1/3/8"
    assert res["event"]["payload"] == [52, 69]
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    res = await client.receive_json()
    assert res["event"]["destination"] == "1/2/4"
    assert res["event"]["payload"] == 1
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert (
        res["event"]["source"] == "0.0.0"
    )  # needs to be the IA currently connected to
    assert res["event"]["direction"] == "Outgoing"
    assert res["event"]["timestamp"] is not None

    res = await client.receive_json()
    assert res["event"]["destination"] == "1/2/5"
    assert res["event"]["payload"] is None
    assert res["event"]["telegramtype"] == "SecureAPDU"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None