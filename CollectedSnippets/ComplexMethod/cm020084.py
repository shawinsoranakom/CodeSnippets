async def test_update_entity_error(
    hass: HomeAssistant,
    knx: KNXTestKit,
    hass_ws_client: WebSocketGenerator,
    create_ui_entity: KnxEntityGenerator,
) -> None:
    """Test entity update."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    test_entity = await create_ui_entity(
        platform=Platform.SWITCH,
        knx_data={"ga_switch": {"write": "1/2/3"}},
        entity_data={"name": "Test"},
    )

    # update unsupported platform
    new_name = "Updated name"
    new_ga_switch_write = "4/5/6"
    await client.send_json_auto_id(
        {
            "type": "knx/update_entity",
            "platform": Platform.TTS,
            "entity_id": test_entity.entity_id,
            "data": {
                "entity": {"name": new_name},
                "knx": {"ga_switch": {"write": new_ga_switch_write}},
            },
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert not res["result"]["success"]
    assert res["result"]["errors"][0]["path"] == ["platform"]
    assert res["result"]["error_base"].startswith("value must be one of")

    # entity not found
    await client.send_json_auto_id(
        {
            "type": "knx/update_entity",
            "platform": Platform.SWITCH,
            "entity_id": "non_existing_entity_id",
            "data": {
                "entity": {"name": new_name},
                "knx": {"ga_switch": {"write": new_ga_switch_write}},
            },
        }
    )
    res = await client.receive_json()
    assert not res["success"], res
    assert res["error"]["code"] == "home_assistant_error"
    assert res["error"]["message"].startswith("Entity not found:")

    # entity not in storage
    await client.send_json_auto_id(
        {
            "type": "knx/update_entity",
            "platform": Platform.SWITCH,
            # `sensor` isn't yet supported, but we only have sensor entities automatically
            # created with no configuration - it doesn't ,atter for the test though
            "entity_id": "sensor.knx_interface_individual_address",
            "data": {
                "entity": {"name": new_name},
                "knx": {"ga_switch": {"write": new_ga_switch_write}},
            },
        }
    )
    res = await client.receive_json()
    assert not res["success"], res
    assert res["error"]["code"] == "home_assistant_error"
    assert res["error"]["message"].startswith("Entity not found in storage")