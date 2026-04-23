async def test_logbook_context_from_template(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

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
    await hass.async_block_till_done()

    # First state change (should be logged)
    hass.states.async_set("switch.test_state", STATE_OFF)
    await hass.async_block_till_done()

    switch_turn_off_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set(
        "switch.test_state", STATE_ON, context=switch_turn_off_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    # Today time 00:00:00
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    # Test today entries with filter by end_time
    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert json_dict[0]["domain"] == "homeassistant"
    assert "context_entity_id" not in json_dict[0]

    assert json_dict[1]["entity_id"] == "switch.test_template_switch"

    assert json_dict[2]["entity_id"] == "switch.test_state"

    assert json_dict[3]["entity_id"] == "switch.test_template_switch"
    assert json_dict[3]["context_entity_id"] == "switch.test_state"
    assert json_dict[3]["context_entity_id_name"] == "test state"

    assert json_dict[4]["entity_id"] == "switch.test_state"
    assert json_dict[4]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    assert json_dict[5]["entity_id"] == "switch.test_template_switch"
    assert json_dict[5]["context_entity_id"] == "switch.test_state"
    assert json_dict[5]["context_entity_id_name"] == "test state"
    assert json_dict[5]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"