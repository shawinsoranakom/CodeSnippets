async def test_get_events_with_context_state(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook get_events with a context state."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("light.kitchen1", STATE_OFF)
    hass.states.async_set("light.kitchen2", STATE_OFF)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("binary_sensor.is_light", STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(
        "light.kitchen1", STATE_ON, {"brightness": 100}, context=context
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "light.kitchen2", STATE_ON, {"brightness": 200}, context=context
    )
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 1
    results = response["result"]
    assert results[1]["entity_id"] == "binary_sensor.is_light"
    assert results[1]["state"] == "off"
    assert "context_state" not in results[1]
    assert results[2]["entity_id"] == "light.kitchen1"
    assert results[2]["state"] == "on"
    assert results[2]["context_entity_id"] == "binary_sensor.is_light"
    assert results[2]["context_state"] == "off"
    assert results[2]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"
    assert "context_event_type" not in results[2]
    assert results[3]["entity_id"] == "light.kitchen2"
    assert results[3]["state"] == "on"
    assert results[3]["context_entity_id"] == "binary_sensor.is_light"
    assert results[3]["context_state"] == "off"
    assert results[3]["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"
    assert "context_event_type" not in results[3]