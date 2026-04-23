async def test_sending_location(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
    extra_webhook_data: dict[str, Any],
    expected_attributes: dict[str, Any],
    expected_state: str,
) -> None:
    """Test sending a location via a webhook."""
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={
            "type": "update_location",
            "data": {
                "gps_accuracy": 30,
                "battery": 40,
                "altitude": 50,
                "course": 60,
                "speed": 70,
                "vertical_accuracy": 80,
            }
            | extra_webhook_data,
        },
    )

    assert resp.status == HTTPStatus.OK
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.test_1_2")
    assert state is not None
    assert state.name == "Test 1"
    assert state.state == expected_state
    assert (
        state.attributes
        == {
            "friendly_name": "Test 1",
            "source_type": "gps",
            "battery_level": 40,
            "altitude": 50.0,
            "course": 60,
            "speed": 70,
            "vertical_accuracy": 80,
        }
        | expected_attributes
    )

    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={
            "type": "update_location",
            "data": {
                "gps": [1, 2],
                "gps_accuracy": 3,
                "battery": 4,
                "altitude": 5,
                "course": 6,
                "speed": 7,
                "vertical_accuracy": 8,
                "location_name": "",
            },
        },
    )

    assert resp.status == HTTPStatus.OK
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.test_1_2")
    assert state is not None
    assert state.state == "not_home"
    assert state.attributes == {
        "friendly_name": "Test 1",
        "source_type": "gps",
        "latitude": 1.0,
        "longitude": 2.0,
        "gps_accuracy": 3,
        "battery_level": 4,
        "altitude": 5.0,
        "course": 6,
        "speed": 7,
        "vertical_accuracy": 8,
        "in_zones": [],
    }