async def test_restoring_location(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test sending a location via a webhook."""
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={
            "type": "update_location",
            "data": {
                "gps": [10, 20],
                "gps_accuracy": 30,
                "battery": 40,
                "altitude": 50,
                "course": 60,
                "speed": 70,
                "vertical_accuracy": 80,
            },
        },
    )

    assert resp.status == HTTPStatus.OK
    await hass.async_block_till_done()
    state_1 = hass.states.get("device_tracker.test_1_2")
    assert state_1 is not None

    config_entry = hass.config_entries.async_entries("mobile_app")[1]

    # mobile app doesn't support unloading, so we just reload device tracker
    await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.DEVICE_TRACKER
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.DEVICE_TRACKER]
    )
    await hass.async_block_till_done()

    state_2 = hass.states.get("device_tracker.test_1_2")
    assert state_2 is not None

    assert state_1 is not state_2
    assert state_2.name == "Test 1"
    assert state_2.state == "not_home"
    assert state_2.attributes["source_type"] == "gps"
    assert state_2.attributes["latitude"] == 10
    assert state_2.attributes["longitude"] == 20
    assert state_2.attributes["gps_accuracy"] == 30
    assert state_2.attributes["battery_level"] == 40
    assert state_2.attributes["altitude"] == 50
    assert state_2.attributes["course"] == 60
    assert state_2.attributes["speed"] == 70
    assert state_2.attributes["vertical_accuracy"] == 80