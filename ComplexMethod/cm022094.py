async def test_subscribe_unsubscribe_logbook_stream_excluded_entities(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream with excluded entities."""
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
                CONF_EXCLUDE: {
                    CONF_ENTITIES: ["light.exc"],
                    CONF_DOMAINS: ["switch"],
                    CONF_ENTITY_GLOBS: ["*.excluded"],
                }
            },
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set("light.exc", STATE_ON)
    hass.states.async_set("light.exc", STATE_OFF)
    hass.states.async_set("switch.any", STATE_ON)
    hass.states.async_set("switch.any", STATE_OFF)
    hass.states.async_set("cover.excluded", STATE_ON)
    hass.states.async_set("cover.excluded", STATE_OFF)

    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    state: State = hass.states.get("binary_sensor.is_light")
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
        {
            "entity_id": "binary_sensor.is_light",
            "state": "off",
            "when": state.last_updated_timestamp,
        }
    ]
    assert msg["event"]["start_time"] == now.timestamp()
    assert msg["event"]["end_time"] > msg["event"]["start_time"]
    assert msg["event"]["partial"] is True

    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == []

    hass.states.async_set("light.exc", STATE_ON)
    hass.states.async_set("light.exc", STATE_OFF)
    hass.states.async_set("switch.any", STATE_ON)
    hass.states.async_set("switch.any", STATE_OFF)
    hass.states.async_set("cover.excluded", STATE_ON)
    hass.states.async_set("cover.excluded", STATE_OFF)
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
    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

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

    await async_wait_recording_done(hass)
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
        {ATTR_NAME: "Mock automation 3", ATTR_ENTITY_ID: "light.keep"},
    )
    hass.states.async_set("cover.excluded", STATE_ON)
    hass.states.async_set("cover.excluded", STATE_OFF)
    await hass.async_block_till_done()
    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
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
            "entity_id": "light.keep",
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