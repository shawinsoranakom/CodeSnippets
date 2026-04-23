async def test_history_during_period_for_invalid_entity_ids(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test history_during_period for valid and invalid entity ids."""
    now = dt_util.utcnow()

    await async_setup_component(hass, "history", {})
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)
    hass.states.async_set("sensor.one", "on", attributes={"any": "attr"})
    sensor_one_last_updated_timestamp = hass.states.get(
        "sensor.one"
    ).last_updated_timestamp
    await async_recorder_block_till_done(hass)
    hass.states.async_set("sensor.two", "off", attributes={"any": "attr"})
    sensor_two_last_updated_timestamp = hass.states.get(
        "sensor.two"
    ).last_updated_timestamp
    await async_recorder_block_till_done(hass)
    hass.states.async_set("sensor.three", "off", attributes={"any": "again"})
    await async_recorder_block_till_done(hass)
    await async_wait_recording_done(hass)
    await async_wait_recording_done(hass)

    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.one"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response == {
        "result": {
            "sensor.one": [
                {
                    "a": {},
                    "lu": pytest.approx(sensor_one_last_updated_timestamp),
                    "s": "on",
                }
            ],
        },
        "id": 1,
        "type": "result",
        "success": True,
    }

    await client.send_json(
        {
            "id": 2,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.one", "sensor.two"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response == {
        "result": {
            "sensor.one": [
                {
                    "a": {},
                    "lu": pytest.approx(sensor_one_last_updated_timestamp),
                    "s": "on",
                }
            ],
            "sensor.two": [
                {
                    "a": {},
                    "lu": pytest.approx(sensor_two_last_updated_timestamp),
                    "s": "off",
                }
            ],
        },
        "id": 2,
        "type": "result",
        "success": True,
    }

    await client.send_json(
        {
            "id": 3,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["sens!or.one", "two"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"] is False
    assert response == {
        "error": {
            "code": "invalid_entity_ids",
            "message": "Invalid entity_ids",
        },
        "id": 3,
        "type": "result",
        "success": False,
    }

    await client.send_json(
        {
            "id": 4,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.one", "sensortwo."],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"] is False
    assert response == {
        "error": {
            "code": "invalid_entity_ids",
            "message": "Invalid entity_ids",
        },
        "id": 4,
        "type": "result",
        "success": False,
    }

    await client.send_json(
        {
            "id": 5,
            "type": "history/history_during_period",
            "start_time": now.isoformat(),
            "entity_ids": ["one", ".sensortwo"],
            "include_start_time_state": True,
            "significant_changes_only": False,
            "no_attributes": True,
        }
    )
    response = await client.receive_json()
    assert response["success"] is False
    assert response == {
        "error": {
            "code": "invalid_entity_ids",
            "message": "Invalid entity_ids",
        },
        "id": 5,
        "type": "result",
        "success": False,
    }