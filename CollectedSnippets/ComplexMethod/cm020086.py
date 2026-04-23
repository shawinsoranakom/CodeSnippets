async def test_validate_entity(
    hass: HomeAssistant,
    knx: KNXTestKit,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test entity validation."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    # valid data
    await client.send_json_auto_id(
        {
            "type": "knx/validate_entity",
            "platform": Platform.SWITCH,
            "data": {
                "entity": {"name": "test_name"},
                "knx": {"ga_switch": {"write": "1/2/3"}},
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["success"] is True

    # invalid data
    await client.send_json_auto_id(
        {
            "type": "knx/validate_entity",
            "platform": Platform.SWITCH,
            "data": {
                "entity": {"name": "test_name"},
                "knx": {"ga_switch": {}},
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["success"] is False
    assert res["result"]["errors"][0]["path"] == ["data", "knx", "ga_switch", "write"]
    assert res["result"]["errors"][0]["error_message"] == "required key not provided"
    assert res["result"]["error_base"].startswith("required key not provided")

    # invalid group_select data
    await client.send_json_auto_id(
        {
            "type": "knx/validate_entity",
            "platform": Platform.LIGHT,
            "data": {
                "entity": {"name": "test_name"},
                "knx": {
                    "color": {
                        "ga_red_brightness": {"write": "1/2/3"},
                        "ga_green_brightness": {"write": "1/2/4"},
                        # ga_blue_brightness is missing - which is required
                    }
                },
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["success"] is False
    # This shall test that a required key of the second GroupSelect schema is missing
    # and not yield the "extra keys not allowed" error of the first GroupSelect Schema
    assert res["result"]["errors"][0]["path"] == [
        "data",
        "knx",
        "color",
        "ga_blue_brightness",
    ]
    assert res["result"]["errors"][0]["error_message"] == "required key not provided"
    assert res["result"]["error_base"].startswith("required key not provided")