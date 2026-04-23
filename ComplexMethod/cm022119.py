async def test_logbook_stream_live_parent_service_call_only(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test user attribution when parent context only appears on a service call.

    In the thermostat pattern, the parent context also appears on a state
    change for climate.living_room. This test covers the case where the
    parent context ONLY fires a call_service event (no state change with
    the parent context for any subscribed entity). The live consumer must
    still resolve the child's user_id from the parent's call_service event.

    This fails if EVENT_CALL_SERVICE is not subscribed to in the live stream.
    """
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await hass.async_block_till_done()

    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    now = dt_util.utcnow()
    websocket_client = await hass_ws_client()
    end_time = now + timedelta(hours=3)
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "end_time": end_time.isoformat(),
            "entity_ids": ["switch.heater"],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # Drain historical backfill
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["partial"] is True

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["events"] == []

    # Stream is now live. Fire a parent service call (no state change with
    # the parent context) followed by a child state change.
    user_id = "b400facee45711eaa9308bfd3d19e474"
    parent_context = core.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id=user_id,
    )
    child_context = core.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id=parent_context.id,
    )

    # Only the service call carries the parent context — no state change
    # with parent_context for any subscribed entity.
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "homeassistant",
            ATTR_SERVICE: "turn_on",
            "service_data": {ATTR_ENTITY_ID: "switch.heater"},
        },
        context=parent_context,
    )

    # Child state change with no user_id on its context
    hass.states.async_set(
        "switch.heater",
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Heater"},
        context=child_context,
    )
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"

    heater_entries = [
        e for e in msg["event"]["events"] if e.get("entity_id") == "switch.heater"
    ]
    assert len(heater_entries) == 1
    assert heater_entries[0]["state"] == "on"
    assert heater_entries[0]["context_user_id"] == user_id