async def test_create_entity_error(
    hass: HomeAssistant,
    knx: KNXTestKit,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test unsuccessful entity creation."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    # create entity with invalid platform
    await client.send_json_auto_id(
        {
            "type": "knx/create_entity",
            "platform": "invalid_platform",
            "data": {
                "entity": {"name": "Test invalid platform"},
                "knx": {"ga_switch": {"write": "1/2/3"}},
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert not res["result"]["success"]
    assert res["result"]["errors"][0]["path"] == ["platform"]
    assert res["result"]["error_base"].startswith("expected EntityPlatforms or one of")

    # create entity with unsupported platform
    await client.send_json_auto_id(
        {
            "type": "knx/create_entity",
            "platform": Platform.TTS,  # "tts" is not a supported platform (and is unlikely to ever be)
            "data": {
                "entity": {"name": "Test invalid platform"},
                "knx": {"ga_switch": {"write": "1/2/3"}},
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert not res["result"]["success"]
    assert res["result"]["errors"][0]["path"] == ["platform"]
    assert res["result"]["error_base"].startswith("value must be one of")