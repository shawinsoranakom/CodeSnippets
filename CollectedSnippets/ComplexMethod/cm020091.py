async def test_knx_subscribe_telegrams_command_project(
    hass: HomeAssistant,
    knx: KNXTestKit,
    hass_ws_client: WebSocketGenerator,
    load_knxproj: None,
) -> None:
    """Test knx/subscribe_telegrams command with project data."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "knx/subscribe_telegrams"})
    res = await client.receive_json()
    assert res["success"], res

    # incoming DPT 1 telegram
    await knx.receive_write("0/0/1", True)
    res = await client.receive_json()
    assert res["event"]["destination"] == "0/0/1"
    assert res["event"]["destination_name"] == "Binary"
    assert res["event"]["payload"] == 1
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.2.3"
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    # incoming DPT 5 telegram
    await knx.receive_write("0/1/1", (0x50,), source="1.1.6")
    res = await client.receive_json()
    assert res["event"]["destination"] == "0/1/1"
    assert res["event"]["destination_name"] == "percent"
    assert res["event"]["payload"] == [
        80,
    ]
    assert res["event"]["value"] == 31
    assert res["event"]["unit"] == "%"
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.1.6"
    assert (
        res["event"]["source_name"]
        == "Enertex Bayern GmbH Enertex KNX LED Dimmsequenzer 20A/5x REG"
    )
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None

    # incoming undecodable telegram (wrong payload type)
    await knx.receive_write("0/1/1", True, source="1.1.6")
    res = await client.receive_json()
    assert res["event"]["destination"] == "0/1/1"
    assert res["event"]["destination_name"] == "percent"
    assert res["event"]["payload"] == 1
    assert res["event"]["value"] is None
    assert res["event"]["telegramtype"] == "GroupValueWrite"
    assert res["event"]["source"] == "1.1.6"
    assert (
        res["event"]["source_name"]
        == "Enertex Bayern GmbH Enertex KNX LED Dimmsequenzer 20A/5x REG"
    )
    assert res["event"]["direction"] == "Incoming"
    assert res["event"]["timestamp"] is not None