async def test_history_during_period_significant_domain(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    time_zone,
) -> None:
    """Test history_during_period with climate domain."""
    await hass.config.async_set_time_zone(time_zone)
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
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {}

    await client.send_json(
        {
            "id": 2,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
            "minimal_response": True,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 2

    sensor_test_history = response["result"]["climate.test"]
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
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": False,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 3
    sensor_test_history = response["result"]["climate.test"]

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
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": True,
            "no_attributes": False,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 4
    sensor_test_history = response["result"]["climate.test"]

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
            "type": "history/history_during_period",
            "start_time": later.isoformat(),
            "entity_ids": ["climate.test"],
            "include_start_time_state": True,
            "significant_changes_only": True,
            "no_attributes": False,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 5
    sensor_test_history = response["result"]["climate.test"]

    assert len(sensor_test_history) == 1

    assert sensor_test_history[0]["s"] == "on"
    assert sensor_test_history[0]["a"] == {"temperature": "5"}
    assert sensor_test_history[0]["lu"] == later.timestamp()
    assert "lc" not in sensor_test_history[0]