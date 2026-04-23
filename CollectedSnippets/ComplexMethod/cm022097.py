async def test_subscribe_unsubscribe_logbook_stream(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await hass.async_block_till_done()

    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    state: State = hass.states.get("binary_sensor.is_light")
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    init_listeners = {
        **init_listeners,
        EVENT_HOMEASSISTANT_START: init_listeners[EVENT_HOMEASSISTANT_START] - 1,
    }
    await websocket_client.send_json(
        {"id": 7, "type": "logbook/event_stream", "start_time": now.isoformat()}
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": "off",
            "when": state.last_updated_timestamp,
        }
    ]
    assert msg["event"]["start_time"] == now.timestamp()
    assert msg["event"]["end_time"] > msg["event"]["start_time"]
    assert msg["event"]["partial"] is True

    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == []

    hass.states.async_set("light.alpha", "on")
    hass.states.async_set("light.alpha", "off")
    alpha_off_state: State = hass.states.get("light.alpha")
    hass.states.async_set("light.zulu", "on", {"color": "blue"})
    hass.states.async_set("light.zulu", "off", {"effect": "help"})
    zulu_off_state: State = hass.states.get("light.zulu")
    hass.states.async_set(
        "light.zulu", "on", {"effect": "help", "color": ["blue", "green"]}
    )
    zulu_on_state: State = hass.states.get("light.zulu")
    await hass.async_block_till_done()

    hass.states.async_remove("light.zulu")
    await hass.async_block_till_done()

    hass.states.async_set("light.zulu", "on", {"effect": "help", "color": "blue"})

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == [
        {
            "entity_id": "light.alpha",
            "state": "off",
            "when": alpha_off_state.last_updated_timestamp,
        },
        {
            "entity_id": "light.zulu",
            "state": "off",
            "when": zulu_off_state.last_updated_timestamp,
        },
        {
            "entity_id": "light.zulu",
            "state": "on",
            "when": zulu_on_state.last_updated_timestamp,
        },
    ]

    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {
            ATTR_NAME: "Mock automation",
            ATTR_ENTITY_ID: "automation.mock_automation",
            ATTR_SOURCE: "numeric state of sensor.hungry_dogs",
        },
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {
            ATTR_NAME: "Mock script",
            ATTR_ENTITY_ID: "script.mock_script",
            ATTR_SOURCE: "numeric state of sensor.hungry_dogs",
        },
    )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": "automation.mock_automation",
            "message": "triggered by numeric state of sensor.hungry_dogs",
            "name": "Mock automation",
            "source": "numeric state of sensor.hungry_dogs",
            "when": ANY,
        },
        {
            "context_id": ANY,
            "domain": "script",
            "entity_id": "script.mock_script",
            "message": "started",
            "name": "Mock script",
            "when": ANY,
        },
        {
            "domain": "homeassistant",
            "icon": "mdi:home-assistant",
            "message": "started",
            "name": "Home Assistant",
            "when": ANY,
        },
    ]

    context = core.Context(
        id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {
            ATTR_NAME: "Mock automation",
            ATTR_ENTITY_ID: automation_entity_id_test,
            ATTR_SOURCE: "state of binary_sensor.dog_food_ready",
        },
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
    hass.states.async_set(entity_id_test, STATE_ON, context=context)
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=context)
    hass.states.async_set(entity_id_second, STATE_ON, context=context)

    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "context_id": "01GTDGKBCH00GW0X276W5TEDDD",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "domain": "automation",
            "entity_id": "automation.alarm",
            "message": "triggered by state of binary_sensor.dog_food_ready",
            "name": "Mock automation",
            "source": "state of binary_sensor.dog_food_ready",
            "when": ANY,
        },
        {
            "context_domain": "automation",
            "context_entity_id": "automation.alarm",
            "context_event_type": "automation_triggered",
            "context_id": "01GTDGKBCH00GW0X276W5TEDDD",
            "context_message": "triggered by state of binary_sensor.dog_food_ready",
            "context_name": "Mock automation",
            "context_source": "state of binary_sensor.dog_food_ready",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "domain": "script",
            "entity_id": "script.mock_script",
            "message": "started",
            "name": "Mock script",
            "when": ANY,
        },
        {
            "context_domain": "automation",
            "context_entity_id": "automation.alarm",
            "context_event_type": "automation_triggered",
            "context_message": "triggered by state of binary_sensor.dog_food_ready",
            "context_name": "Mock automation",
            "context_source": "state of binary_sensor.dog_food_ready",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "entity_id": "alarm_control_panel.area_001",
            "state": "on",
            "when": ANY,
        },
        {
            "context_domain": "automation",
            "context_entity_id": "automation.alarm",
            "context_event_type": "automation_triggered",
            "context_message": "triggered by state of binary_sensor.dog_food_ready",
            "context_name": "Mock automation",
            "context_source": "state of binary_sensor.dog_food_ready",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "entity_id": "alarm_control_panel.area_002",
            "state": "on",
            "when": ANY,
        },
    ]
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation 2", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )

    await hass.async_block_till_done()

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "context_domain": "automation",
            "context_entity_id": "automation.alarm",
            "context_event_type": "automation_triggered",
            "context_id": "01GTDGKBCH00GW0X276W5TEDDD",
            "context_message": "triggered by state of binary_sensor.dog_food_ready",
            "context_name": "Mock automation",
            "context_source": "state of binary_sensor.dog_food_ready",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "domain": "automation",
            "entity_id": "automation.alarm",
            "message": "triggered",
            "name": "Mock automation 2",
            "source": None,
            "when": ANY,
        }
    ]

    await async_wait_recording_done(hass)
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation 3", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )

    await hass.async_block_till_done()
    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "context_domain": "automation",
            "context_entity_id": "automation.alarm",
            "context_event_type": "automation_triggered",
            "context_id": "01GTDGKBCH00GW0X276W5TEDDD",
            "context_message": "triggered by state of binary_sensor.dog_food_ready",
            "context_name": "Mock automation",
            "context_source": "state of binary_sensor.dog_food_ready",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "domain": "automation",
            "entity_id": "automation.alarm",
            "message": "triggered",
            "name": "Mock automation 3",
            "source": None,
            "when": ANY,
        }
    ]

    await websocket_client.send_json(
        {"id": 8, "type": "unsubscribe_events", "subscription": 7}
    )
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)

    assert msg["id"] == 8
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)