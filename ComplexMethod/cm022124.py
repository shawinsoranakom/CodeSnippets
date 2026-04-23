async def test_exclude_removed_entities(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test if events are excluded on last update."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    entity_id = "climate.bla"
    entity_id2 = "climate.blu"

    hass.states.async_set(entity_id, STATE_ON)
    hass.states.async_set(entity_id, STATE_OFF)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set(entity_id2, STATE_ON)
    hass.states.async_set(entity_id2, STATE_OFF)

    hass.states.async_remove(entity_id)
    hass.states.async_remove(entity_id2)

    await async_wait_recording_done(hass)

    client = await hass_client()

    # Today time 00:00:00
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    # Test today entries without filters
    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    assert response.status == HTTPStatus.OK
    response_json = await response.json()

    assert len(response_json) == 3
    assert response_json[0]["entity_id"] == entity_id
    assert response_json[1]["domain"] == "homeassistant"
    assert response_json[1]["message"] == "started"
    assert response_json[2]["entity_id"] == entity_id2