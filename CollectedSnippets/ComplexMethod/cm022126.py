async def test_logbook_context_id_automation_script_started_manually(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook populates context_ids for scripts and automations started manually."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    # An Automation
    automation_entity_id_test = "automation.alarm"
    automation_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVCCC",
        user_id="f400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=automation_context,
    )
    script_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=script_context,
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    script_2_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVEEE",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script"},
        context=script_2_context,
    )
    hass.states.async_set("switch.new", STATE_ON, context=script_2_context)
    hass.states.async_set("switch.new", STATE_OFF, context=script_2_context)

    await hass.async_block_till_done()
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

    assert json_dict[0]["entity_id"] == "automation.alarm"
    assert "context_entity_id" not in json_dict[0]
    assert json_dict[0]["context_user_id"] == "f400facee45711eaa9308bfd3d19e474"
    assert json_dict[0]["context_id"] == "01GTDGKBCH00GW0X476W5TVCCC"

    assert json_dict[1]["entity_id"] == "script.mock_script"
    assert "context_entity_id" not in json_dict[1]
    assert json_dict[1]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"
    assert json_dict[1]["context_id"] == "01GTDGKBCH00GW0X476W5TVAAA"

    assert json_dict[2]["domain"] == "homeassistant"

    assert json_dict[3]["entity_id"] is None
    assert json_dict[3]["name"] == "Mock script"
    assert "context_entity_id" not in json_dict[1]
    assert json_dict[3]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"
    assert json_dict[3]["context_id"] == "01GTDGKBCH00GW0X476W5TVEEE"

    assert json_dict[4]["entity_id"] == "switch.new"
    assert json_dict[4]["state"] == "off"
    assert "context_entity_id" not in json_dict[1]
    assert json_dict[4]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"
    assert json_dict[4]["context_event_type"] == "script_started"
    assert json_dict[4]["context_domain"] == "script"