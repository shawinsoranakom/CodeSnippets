async def test_sensor_id_no_dupes(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a duplicate unique ID in registration updates the sensor."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    payload = {
        "type": "register_sensor",
        "data": {
            "attributes": {"foo": "bar"},
            "device_class": "battery",
            "icon": "mdi:battery",
            "name": "Battery State",
            "state": 100,
            "type": "sensor",
            "unique_id": "battery_state",
            "unit_of_measurement": PERCENTAGE,
        },
    }

    reg_resp = await webhook_client.post(webhook_url, json=payload)

    assert reg_resp.status == HTTPStatus.CREATED

    reg_json = await reg_resp.json()
    assert reg_json == {"success": True}
    await hass.async_block_till_done()

    assert "Re-register" not in caplog.text

    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None

    assert entity.attributes["device_class"] == "battery"
    assert entity.attributes["icon"] == "mdi:battery"
    assert entity.attributes["unit_of_measurement"] == PERCENTAGE
    assert entity.attributes["foo"] == "bar"
    assert entity.domain == "sensor"
    assert entity.name == "Test 1 Battery State"
    assert entity.state == "100"

    payload["data"]["state"] = 99
    dupe_resp = await webhook_client.post(webhook_url, json=payload)

    assert dupe_resp.status == HTTPStatus.CREATED
    dupe_reg_json = await dupe_resp.json()
    assert dupe_reg_json == {"success": True}
    await hass.async_block_till_done()

    assert "Re-register" in caplog.text

    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None

    assert entity.attributes["device_class"] == "battery"
    assert entity.attributes["icon"] == "mdi:battery"
    assert entity.attributes["unit_of_measurement"] == PERCENTAGE
    assert entity.attributes["foo"] == "bar"
    assert entity.domain == "sensor"
    assert entity.name == "Test 1 Battery State"
    assert entity.state == "99"