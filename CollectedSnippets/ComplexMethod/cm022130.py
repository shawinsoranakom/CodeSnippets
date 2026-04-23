async def test_logbook_multiple_entities(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view with a multiple entities."""
    await async_setup_component(hass, "logbook", {})
    assert await async_setup_component(
        hass,
        "switch",
        {
            "switch": {
                "platform": "template",
                "switches": {
                    "test_template_switch": {
                        "value_template": "{{ states.switch.test_state.state }}",
                        "turn_on": {
                            "service": "switch.turn_on",
                            "entity_id": "switch.test_state",
                        },
                        "turn_off": {
                            "service": "switch.turn_off",
                            "entity_id": "switch.test_state",
                        },
                    }
                },
            }
        },
    )
    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    # Entity added (should not be logged)
    hass.states.async_set("switch.test_state", STATE_ON)
    hass.states.async_set("light.test_state", STATE_ON)
    hass.states.async_set("binary_sensor.test_state", STATE_ON)

    await hass.async_block_till_done()

    # First state change (should be logged)
    hass.states.async_set("switch.test_state", STATE_OFF)
    hass.states.async_set("light.test_state", STATE_OFF)
    hass.states.async_set("binary_sensor.test_state", STATE_OFF)

    await hass.async_block_till_done()

    switch_turn_off_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set(
        "switch.test_state", STATE_ON, context=switch_turn_off_context
    )
    hass.states.async_set("light.test_state", STATE_ON, context=switch_turn_off_context)
    hass.states.async_set(
        "binary_sensor.test_state", STATE_ON, context=switch_turn_off_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    # Today time 00:00:00
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    # Test today entries with filter by end_time
    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=switch.test_state,light.test_state"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert len(json_dict) == 4

    assert json_dict[0]["entity_id"] == "switch.test_state"

    assert json_dict[1]["entity_id"] == "light.test_state"

    assert json_dict[2]["entity_id"] == "switch.test_state"
    assert json_dict[2]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    assert json_dict[3]["entity_id"] == "light.test_state"
    assert json_dict[3]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    # Test today entries with filter by end_time
    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=binary_sensor.test_state,light.test_state"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert len(json_dict) == 4

    assert json_dict[0]["entity_id"] == "light.test_state"

    assert json_dict[1]["entity_id"] == "binary_sensor.test_state"

    assert json_dict[2]["entity_id"] == "light.test_state"
    assert json_dict[2]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    assert json_dict[3]["entity_id"] == "binary_sensor.test_state"
    assert json_dict[3]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    # Test today entries with filter by end_time
    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=light.test_state,binary_sensor.test_state"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert len(json_dict) == 4

    assert json_dict[0]["entity_id"] == "light.test_state"

    assert json_dict[1]["entity_id"] == "binary_sensor.test_state"

    assert json_dict[2]["entity_id"] == "light.test_state"
    assert json_dict[2]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    assert json_dict[3]["entity_id"] == "binary_sensor.test_state"
    assert json_dict[3]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"