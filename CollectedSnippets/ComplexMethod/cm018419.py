async def test_history_stream_significant_domain_historical_only(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the stream with climate domain with historical states only."""
    now = dt_util.utcnow()

    await async_setup_component(hass, "history", {})
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("climate.test", "on", attributes={"temperature": "1"})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("climate.test", "off", attributes={"temperature": "2"})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("climate.test", "off", attributes={"temperature": "3"})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("climate.test", "off", attributes={"temperature": "4"})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("climate.test", "on", attributes={"temperature": "5"})
    await async_wait_recording_done(hass)

    await async_wait_recording_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "history/stream",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 1
    assert response["type"] == "result"
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response == {
        "event": {
            "end_time": now.timestamp(),
            "start_time": now.timestamp(),
            "states": {},
        },
        "id": 1,
        "type": "event",
    }

    end_time = dt_util.utcnow()
    await client.send_json(
        {
            "id": 2,
            "type": "history/stream",
            "start_time": now.isoformat(),
            "end_time": end_time.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
            "minimal_response": True,
        }
    )
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 2
    assert response["type"] == "result"

    async with asyncio.timeout(3):
        response = await client.receive_json()
    sensor_test_history = response["event"]["states"]["climate.test"]
    assert len(sensor_test_history) == 5

    assert sensor_test_history[0]["s"] == "on"
    assert sensor_test_history[0]["a"] == {}
    assert isinstance(sensor_test_history[0]["lu"], float)
    assert "lc" not in sensor_test_history[0]  # skipped if the same a last_updated (lu)

    assert "a" in sensor_test_history[1]
    assert sensor_test_history[1]["s"] == "off"
    assert "lc" not in sensor_test_history[1]  # skipped if the same a last_updated (lu)

    assert sensor_test_history[4]["s"] == "on"
    assert sensor_test_history[4]["a"] == {}

    await client.send_json(
        {
            "id": 3,
            "type": "history/stream",
            "start_time": now.isoformat(),
            "end_time": end_time.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": False,
        }
    )
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 3
    assert response["type"] == "result"

    async with asyncio.timeout(3):
        response = await client.receive_json()
    sensor_test_history = response["event"]["states"]["climate.test"]

    assert len(sensor_test_history) == 5

    assert sensor_test_history[0]["s"] == "on"
    assert sensor_test_history[0]["a"] == {"temperature": "1"}
    assert isinstance(sensor_test_history[0]["lu"], float)
    assert "lc" not in sensor_test_history[0]  # skipped if the same a last_updated (lu)

    assert sensor_test_history[1]["s"] == "off"
    assert isinstance(sensor_test_history[1]["lu"], float)
    assert "lc" not in sensor_test_history[1]  # skipped if the same a last_updated (lu)
    assert sensor_test_history[1]["a"] == {"temperature": "2"}

    assert sensor_test_history[4]["s"] == "on"
    assert sensor_test_history[4]["a"] == {"temperature": "5"}

    await client.send_json(
        {
            "id": 4,
            "type": "history/stream",
            "start_time": now.isoformat(),
            "end_time": end_time.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": True,
            "no_attributes": False,
        }
    )
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 4
    assert response["type"] == "result"

    async with asyncio.timeout(3):
        response = await client.receive_json()
    sensor_test_history = response["event"]["states"]["climate.test"]

    assert len(sensor_test_history) == 5

    assert sensor_test_history[0]["s"] == "on"
    assert sensor_test_history[0]["a"] == {"temperature": "1"}
    assert isinstance(sensor_test_history[0]["lu"], float)
    assert "lc" not in sensor_test_history[0]  # skipped if the same a last_updated (lu)

    assert sensor_test_history[1]["s"] == "off"
    assert isinstance(sensor_test_history[1]["lu"], float)
    assert "lc" not in sensor_test_history[1]  # skipped if the same a last_updated (lu)
    assert sensor_test_history[1]["a"] == {"temperature": "2"}

    assert sensor_test_history[2]["s"] == "off"
    assert sensor_test_history[2]["a"] == {"temperature": "3"}

    assert sensor_test_history[3]["s"] == "off"
    assert sensor_test_history[3]["a"] == {"temperature": "4"}

    assert sensor_test_history[4]["s"] == "on"
    assert sensor_test_history[4]["a"] == {"temperature": "5"}

    # Test we impute the state time state
    later = dt_util.utcnow()
    await client.send_json(
        {
            "id": 5,
            "type": "history/stream",
            "start_time": later.isoformat(),
            "end_time": later.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": True,
            "no_attributes": False,
        }
    )
    async with asyncio.timeout(3):
        response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 5
    assert response["type"] == "result"

    async with asyncio.timeout(3):
        response = await client.receive_json()
    sensor_test_history = response["event"]["states"]["climate.test"]

    assert len(sensor_test_history) == 1

    assert sensor_test_history[0]["s"] == "on"
    assert sensor_test_history[0]["a"] == {"temperature": "5"}
    assert sensor_test_history[0]["lu"] == later.timestamp()
    assert "lc" not in sensor_test_history[0]