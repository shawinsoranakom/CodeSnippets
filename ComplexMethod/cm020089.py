async def test_knx_subscribe_telegrams_command_recent_telegrams(
    hass: HomeAssistant, knx: KNXTestKit, hass_ws_client: WebSocketGenerator
) -> None:
    """Test knx/subscribe_telegrams command sending recent telegrams."""
    await knx.setup_integration(
        {
            SwitchSchema.PLATFORM: {
                CONF_NAME: "test",
                KNX_ADDRESS: "1/2/4",
            }
        }
    )

    # send incoming telegram
    await knx.receive_write("1/3/4", True)
    # send outgoing telegram
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.test"}, blocking=True
    )
    await knx.assert_write("1/2/4", 1)

    # connect websocket after telegrams have been sent
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "knx/group_monitor_info"})
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["project_loaded"] is False

    recent_tgs = res["result"]["recent_telegrams"]
    assert len(recent_tgs) == 2
    # telegrams are sorted from oldest to newest
    assert recent_tgs[0]["destination"] == "1/3/4"
    assert recent_tgs[0]["payload"] == 1
    assert recent_tgs[0]["telegramtype"] == "GroupValueWrite"
    assert recent_tgs[0]["source"] == "1.2.3"
    assert recent_tgs[0]["direction"] == "Incoming"
    assert isinstance(recent_tgs[0]["timestamp"], str)

    assert recent_tgs[1]["destination"] == "1/2/4"
    assert recent_tgs[1]["payload"] == 1
    assert recent_tgs[1]["telegramtype"] == "GroupValueWrite"
    assert (
        recent_tgs[1]["source"] == "0.0.0"
    )  # needs to be the IA currently connected to
    assert recent_tgs[1]["direction"] == "Outgoing"
    assert isinstance(recent_tgs[1]["timestamp"], str)