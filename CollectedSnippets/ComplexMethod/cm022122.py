async def test_logbook_view_end_time_entity(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view with end_time and entity."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    entity_id_test = "switch.test"
    hass.states.async_set(entity_id_test, STATE_OFF)
    hass.states.async_set(entity_id_test, STATE_ON)
    entity_id_second = "switch.second"
    hass.states.async_set(entity_id_second, STATE_OFF)
    hass.states.async_set(entity_id_second, STATE_ON)
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
    response_json = await response.json()
    assert len(response_json) == 2
    assert response_json[0]["entity_id"] == entity_id_test
    assert response_json[1]["entity_id"] == entity_id_second

    # Test entries for 3 days with filter by entity_id
    end_time = start + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat(), "entity": "switch.test"},
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json) == 1
    assert response_json[0]["entity_id"] == entity_id_test

    # Tomorrow time 00:00:00
    start = dt_util.utcnow()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    # Test entries from today to 3 days with filter by entity_id
    end_time = start_date + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat(), "entity": "switch.test"},
    )
    response_json = await response.json()
    assert response.status == HTTPStatus.OK
    assert len(response_json) == 1
    assert response_json[0]["entity_id"] == entity_id_test