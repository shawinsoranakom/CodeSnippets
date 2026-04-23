async def test_get_events_entities_filtered_away(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook get_events all entities filtered away."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_ON)
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.filtered",
        STATE_ON,
        {"brightness": 100, ATTR_UNIT_OF_MEASUREMENT: "any"},
    )
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_OFF, {"brightness": 200})
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.filtered",
        STATE_OFF,
        {"brightness": 300, ATTR_UNIT_OF_MEASUREMENT: "any"},
    )

    await async_wait_recording_done(hass)
    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 1

    results = response["result"]
    assert results[0]["entity_id"] == "light.kitchen"
    assert results[0]["state"] == "off"

    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.filtered"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 2

    results = response["result"]
    assert len(results) == 0