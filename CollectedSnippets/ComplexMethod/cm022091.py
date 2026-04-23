async def test_get_events(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook get_events."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_OFF)
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 100})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 200})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 300})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 400})
    await hass.async_block_till_done()
    context = core.Context(
        id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    hass.states.async_set("light.kitchen", STATE_OFF, context=context)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.test"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 2
    assert response["result"] == []

    await client.send_json(
        {
            "id": 3,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 3

    results = response["result"]
    assert results[0]["entity_id"] == "light.kitchen"
    assert results[0]["state"] == "on"
    assert results[1]["entity_id"] == "light.kitchen"
    assert results[1]["state"] == "off"

    await client.send_json(
        {
            "id": 4,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 4

    results = response["result"]
    assert len(results) == 3
    assert results[0]["message"] == "started"
    assert results[1]["entity_id"] == "light.kitchen"
    assert results[1]["state"] == "on"
    assert isinstance(results[1]["when"], float)
    assert results[2]["entity_id"] == "light.kitchen"
    assert results[2]["state"] == "off"
    assert isinstance(results[2]["when"], float)

    await client.send_json(
        {
            "id": 5,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "context_id": "01GTDGKBCH00GW0X276W5TEDDD",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 5

    results = response["result"]
    assert len(results) == 1
    assert results[0]["entity_id"] == "light.kitchen"
    assert results[0]["state"] == "off"
    assert isinstance(results[0]["when"], float)