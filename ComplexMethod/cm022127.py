async def test_logbook_entity_context_parent_id(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view links events via context parent_id."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    # An Automation triggering scripts with a new context
    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )

    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=child_context,
    )
    hass.states.async_set(
        automation_entity_id_test,
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Alarm Automation"},
        context=child_context,
    )

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF, context=child_context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_test, STATE_ON, context=child_context)
    await hass.async_block_till_done()
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=child_context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_second, STATE_ON, context=child_context)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_003",
        child_context,
    )
    await hass.async_block_till_done()

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "homeassistant",
        None,
        child_context,
    )
    await hass.async_block_till_done()

    # A state change via service call with the script as the parent
    light_turn_off_service_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        parent_id="01GTDGKBCH00GW0X476W5TVDDD",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("light.switch", STATE_ON)
    await hass.async_block_till_done()

    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "light",
            ATTR_SERVICE: "turn_off",
            ATTR_ENTITY_ID: "light.switch",
        },
        context=light_turn_off_service_context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "light.switch", STATE_OFF, context=light_turn_off_service_context
    )
    await hass.async_block_till_done()

    # An event with a parent event, but the parent event isn't available
    missing_parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TEDDD",
        parent_id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="485cacf93ef84d25a99ced3126b921d2",
    )
    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_009",
        missing_parent_context,
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

    assert json_dict[0]["entity_id"] == "automation.alarm"
    assert "context_entity_id" not in json_dict[0]
    assert json_dict[0]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    # New context, so this looks to be triggered by the Alarm Automation
    assert json_dict[1]["entity_id"] == "script.mock_script"
    assert json_dict[1]["context_event_type"] == "automation_triggered"
    assert json_dict[1]["context_entity_id"] == "automation.alarm"
    assert json_dict[1]["context_entity_id_name"] == "Alarm Automation"
    assert json_dict[1]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[2]["entity_id"] == entity_id_test
    assert json_dict[2]["context_event_type"] == "script_started"
    assert json_dict[2]["context_entity_id"] == "script.mock_script"
    assert json_dict[2]["context_entity_id_name"] == "mock script"
    assert json_dict[2]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[3]["entity_id"] == entity_id_second
    assert json_dict[3]["context_event_type"] == "script_started"
    assert json_dict[3]["context_entity_id"] == "script.mock_script"
    assert json_dict[3]["context_entity_id_name"] == "mock script"
    assert json_dict[3]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[4]["domain"] == "homeassistant"

    assert json_dict[5]["entity_id"] == "alarm_control_panel.area_003"
    assert json_dict[5]["context_event_type"] == "script_started"
    assert json_dict[5]["context_entity_id"] == "script.mock_script"
    assert json_dict[5]["domain"] == "alarm_control_panel"
    assert json_dict[5]["context_entity_id_name"] == "mock script"
    assert json_dict[5]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[6]["domain"] == "homeassistant"
    assert json_dict[6]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[7]["entity_id"] == "light.switch"
    assert json_dict[7]["context_event_type"] == "call_service"
    assert json_dict[7]["context_domain"] == "light"
    assert json_dict[7]["context_service"] == "turn_off"
    assert json_dict[7]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"

    assert json_dict[8]["entity_id"] == "alarm_control_panel.area_009"
    assert json_dict[8]["domain"] == "alarm_control_panel"
    assert "context_event_type" not in json_dict[8]
    assert "context_entity_id" not in json_dict[8]
    assert "context_entity_id_name" not in json_dict[8]
    assert json_dict[8]["context_user_id"] == "485cacf93ef84d25a99ced3126b921d2"