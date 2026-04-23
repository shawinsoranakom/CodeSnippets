async def test_clean_segments_command(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test cleaning segments and repair flow."""
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    entity_registry.async_get_or_create(
        vacuum.DOMAIN,
        mqtt.DOMAIN,
        "veryunique",
        config_entry=config_entry,
        suggested_object_id="test",
    )
    entity_registry.async_update_entity_options(
        "vacuum.test",
        vacuum.DOMAIN,
        {
            "area_mapping": {"Nabu Casa": ["1", "2"]},
            "last_seen_segments": [
                {"id": "1", "name": "Livingroom"},
                {"id": "2", "name": "Kitchen"},
            ],
        },
    )
    mqtt_mock = await mqtt_mock_entry()
    await hass.async_block_till_done()
    message = """{
        "battery_level": 54,
        "state": "idle",
        "segments":{
            "1":"Livingroom",
            "2":"Kitchen"
        }
    }"""
    async_fire_mqtt_message(hass, "vacuum/state", message)
    await hass.async_block_till_done()
    state = hass.states.get("vacuum.test")
    assert state.state == VacuumActivity.IDLE
    assert (
        state.attributes.get(ATTR_SUPPORTED_FEATURES)
        & vacuum.VacuumEntityFeature.CLEAN_AREA
    )

    issue_registry = ir.async_get(hass)
    # We do not expect a repair flow as the segments did not change
    assert len(issue_registry.issues) == 0

    await common.async_clean_area(hass, ["Nabu Casa"], entity_id="vacuum.test")
    assert (
        call("vacuum/clean_segment", '["1","2"]', 0, False)
        in mqtt_mock.async_publish.mock_calls
    )
    await hass.async_block_till_done()
    message = """{
        "battery_level": 54,
        "state": "cleaning",
        "segments":{
            "1":"Livingroom",
            "2":"Kitchen",
            "3": "Diningroom"
        }
    }"""
    async_fire_mqtt_message(hass, "vacuum/state", message)
    await hass.async_block_till_done()
    # We expect a repair issue now as the available segments have changed
    assert len(issue_registry.issues) == 1

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "vacuum/get_segments", "entity_id": "vacuum.test"}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["segments"] == [
        {"id": "1", "name": "Livingroom", "group": None},
        {"id": "2", "name": "Kitchen", "group": None},
        {"id": "3", "name": "Diningroom", "group": None},
    ]