async def test_logbook_stream_parent_context_bridges_historical_to_live(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test parent-context user attribution bridges the historical→live switch.

    Scenario: a user fires a service call (parent context) that triggers a
    child state change BEFORE the websocket subscription is opened. The
    parent's call_service event lives only in the historical window. After
    the historical backfill completes and the stream switches to live, a
    NEW state change reusing the same child context (whose parent_id points
    back at the historical parent) fires. The live event must inherit the
    user_id from the historical parent — which can only happen if the
    historical pre-pass populated the persistent LRU cache so the live
    consumer can find it.
    """
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await hass.async_block_till_done()

    setup_thermostat_context_test_entities(hass)
    await hass.async_block_till_done()

    user_id = "b400facee45711eaa9308bfd3d19e474"
    parent_context = core.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id=user_id,
    )
    child_context = core.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id=parent_context.id,
    )

    # Fire the parent service call and the first child state change BEFORE
    # the websocket subscription. These will live in the historical window.
    start_time = dt_util.utcnow()
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "climate",
            ATTR_SERVICE: "set_hvac_mode",
            "service_data": {ATTR_ENTITY_ID: "climate.living_room"},
        },
        context=parent_context,
    )
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "homeassistant",
            ATTR_SERVICE: "turn_on",
            "service_data": {ATTR_ENTITY_ID: "switch.heater"},
        },
        context=child_context,
    )
    hass.states.async_set(
        "switch.heater",
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Heater"},
        context=child_context,
    )
    await async_wait_recording_done(hass)

    # Open a filtered subscription. The filtered query path excludes the
    # parent's set_hvac_mode call_service from the historical row stream
    # because its event_data references climate.living_room, not
    # switch.heater. The pre-pass must fetch the parent and populate the
    # persistent LRU so the upcoming live event can resolve attribution.
    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": start_time.isoformat(),
            "entity_ids": ["switch.heater"],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # Drain the historical backfill messages.
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["partial"] is True
    historical_events = msg["event"]["events"]
    historical_heater = [
        e for e in historical_events if e.get("entity_id") == "switch.heater"
    ]
    assert len(historical_heater) == 1
    assert historical_heater[0]["context_user_id"] == user_id

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["events"] == []

    # Stream is now live. Fire a NEW switch.heater state change reusing
    # child_context — its parent_id still points at the historical parent.
    # The live consumer must resolve the user_id via the persistent LRU
    # populated during the historical pre-pass.
    hass.states.async_set(
        "switch.heater",
        STATE_OFF,
        {ATTR_FRIENDLY_NAME: "Heater"},
        context=child_context,
    )
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    live_heater = [
        e for e in msg["event"]["events"] if e.get("entity_id") == "switch.heater"
    ]
    assert len(live_heater) == 1
    assert live_heater[0]["state"] == "off"
    assert live_heater[0]["context_user_id"] == user_id