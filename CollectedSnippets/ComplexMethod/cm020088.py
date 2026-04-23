async def test_knx_group_telegrams_command(
    hass: HomeAssistant, knx: KNXTestKit, hass_ws_client: WebSocketGenerator
) -> None:
    """Test knx/group_telegrams command."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "knx/group_telegrams"})
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"] == {}

    # # get some telegrams to populate the cache
    await knx.receive_write("1/1/1", True)
    await knx.receive_read("2/2/2")  # read telegram shall be ignored
    await knx.receive_write("3/3/3", 0x34)

    await client.send_json_auto_id({"type": "knx/group_telegrams"})
    res = await client.receive_json()
    assert res["success"], res
    assert len(res["result"]) == 2
    assert "1/1/1" in res["result"]
    assert res["result"]["1/1/1"]["destination"] == "1/1/1"
    assert "3/3/3" in res["result"]
    assert res["result"]["3/3/3"]["payload"] == 52
    assert res["result"]["3/3/3"]["telegramtype"] == "GroupValueWrite"
    assert res["result"]["3/3/3"]["source"] == "1.2.3"
    assert res["result"]["3/3/3"]["direction"] == "Incoming"
    assert res["result"]["3/3/3"]["timestamp"] is not None