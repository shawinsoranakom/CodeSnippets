async def test_logbook_entity_context_id(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
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

    # An Automation
    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=context,
    )
    hass.states.async_set(
        automation_entity_id_test,
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Alarm Automation"},
        context=context,
    )

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_test, STATE_ON, context=context)
    await hass.async_block_till_done()
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_second, STATE_ON, context=context)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    await hass.async_add_executor_job(
        logbook.log_entry,
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_003",
        context,
    )
    await hass.async_block_till_done()

    await hass.async_add_executor_job(
        logbook.log_entry,
        hass,
        "mock_name",
        "mock_message",
        "homeassistant",
        None,
        context,
    )
    await hass.async_block_till_done()

    # A service call
    light_turn_off_service_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
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

    assert json_dict[1]["entity_id"] == "script.mock_script"
    assert json_dict[1]["context_event_type"] == "automation_triggered"
    assert json_dict[1]["context_entity_id"] == "automation.alarm"
    assert json_dict[1]["context_entity_id_name"] == "Alarm Automation"
    assert json_dict[1]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[2]["entity_id"] == entity_id_test
    assert json_dict[2]["context_event_type"] == "automation_triggered"
    assert json_dict[2]["context_entity_id"] == "automation.alarm"
    assert json_dict[2]["context_entity_id_name"] == "Alarm Automation"
    assert json_dict[2]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[3]["entity_id"] == entity_id_second
    assert json_dict[3]["context_event_type"] == "automation_triggered"
    assert json_dict[3]["context_entity_id"] == "automation.alarm"
    assert json_dict[3]["context_entity_id_name"] == "Alarm Automation"
    assert json_dict[3]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[4]["domain"] == "homeassistant"

    assert json_dict[5]["entity_id"] == "alarm_control_panel.area_003"
    assert json_dict[5]["context_event_type"] == "automation_triggered"
    assert json_dict[5]["context_entity_id"] == "automation.alarm"
    assert json_dict[5]["domain"] == "alarm_control_panel"
    assert json_dict[5]["context_entity_id_name"] == "Alarm Automation"
    assert json_dict[5]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[6]["domain"] == "homeassistant"
    assert json_dict[6]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"

    assert json_dict[7]["entity_id"] == "light.switch"
    assert json_dict[7]["context_event_type"] == "call_service"
    assert json_dict[7]["context_domain"] == "light"
    assert json_dict[7]["context_service"] == "turn_off"
    assert json_dict[7]["context_user_id"] == "9400facee45711eaa9308bfd3d19e474"