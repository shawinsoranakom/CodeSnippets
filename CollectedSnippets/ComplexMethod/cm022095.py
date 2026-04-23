async def test_subscribe_unsubscribe_logbook_stream_included_entities(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream with included entities."""
    test_entities = (
        "light.inc",
        "switch.any",
        "cover.included",
        "cover.not_included",
        "automation.not_included",
        "binary_sensor.is_light",
    )

    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "automation", "script")
        ]
    )
    await async_setup_component(
        hass,
        logbook.DOMAIN,
        {
            logbook.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_ENTITIES: ["light.inc"],
                    CONF_DOMAINS: ["switch"],
                    CONF_ENTITY_GLOBS: ["*.included"],
                }
            },
        },
    )
    await hass.async_block_till_done()

    for entity_id in test_entities:
        hass.states.async_set(entity_id, STATE_ON)
        hass.states.async_set(entity_id, STATE_OFF)

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
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
        {"entity_id": "light.inc", "state": "off", "when": ANY},
        {"entity_id": "switch.any", "state": "off", "when": ANY},
        {"entity_id": "cover.included", "state": "off", "when": ANY},
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

    for entity_id in test_entities:
        hass.states.async_set(entity_id, STATE_ON)
        hass.states.async_set(entity_id, STATE_OFF)
    await hass.async_block_till_done()

    hass.states.async_remove("light.zulu")
    await hass.async_block_till_done()

    hass.states.async_set("light.zulu", "on", {"effect": "help", "color": "blue"})
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == [
        {"entity_id": "light.inc", "state": "on", "when": ANY},
        {"entity_id": "light.inc", "state": "off", "when": ANY},
        {"entity_id": "switch.any", "state": "on", "when": ANY},
        {"entity_id": "switch.any", "state": "off", "when": ANY},
        {"entity_id": "cover.included", "state": "on", "when": ANY},
        {"entity_id": "cover.included", "state": "off", "when": ANY},
    ]

    for _ in range(3):
        for entity_id in test_entities:
            hass.states.async_set(entity_id, STATE_ON)
            hass.states.async_set(entity_id, STATE_OFF)
        await async_wait_recording_done(hass)

        msg = await websocket_client.receive_json()
        assert msg["id"] == 7
        assert msg["type"] == "event"
        assert msg["event"]["events"] == [
            {"entity_id": "light.inc", "state": "on", "when": ANY},
            {"entity_id": "light.inc", "state": "off", "when": ANY},
            {"entity_id": "switch.any", "state": "on", "when": ANY},
            {"entity_id": "switch.any", "state": "off", "when": ANY},
            {"entity_id": "cover.included", "state": "on", "when": ANY},
            {"entity_id": "cover.included", "state": "off", "when": ANY},
        ]

    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation 3", ATTR_ENTITY_ID: "cover.included"},
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation 3", ATTR_ENTITY_ID: "cover.excluded"},
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {
            ATTR_NAME: "Mock automation switch matching entity",
            ATTR_ENTITY_ID: "switch.match_domain",
        },
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation switch matching domain", ATTR_DOMAIN: "switch"},
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation matches nothing"},
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation 3", ATTR_ENTITY_ID: "light.inc"},
    )

    await hass.async_block_till_done()

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": "cover.included",
            "message": "triggered",
            "name": "Mock automation 3",
            "source": None,
            "when": ANY,
        },
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": "switch.match_domain",
            "message": "triggered",
            "name": "Mock automation switch matching entity",
            "source": None,
            "when": ANY,
        },
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": None,
            "message": "triggered",
            "name": "Mock automation switch matching domain",
            "source": None,
            "when": ANY,
        },
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": None,
            "message": "triggered",
            "name": "Mock automation matches nothing",
            "source": None,
            "when": ANY,
        },
        {
            "context_id": ANY,
            "domain": "automation",
            "entity_id": "light.inc",
            "message": "triggered",
            "name": "Mock automation 3",
            "source": None,
            "when": ANY,
        },
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