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
            "device_class": "plug",
            "icon": "mdi:power-plug",
            "name": "Is Charging",
            "state": True,
            "type": "binary_sensor",
            "unique_id": "is_charging",
        },
    }

    reg_resp = await webhook_client.post(webhook_url, json=payload)

    assert reg_resp.status == HTTPStatus.CREATED

    reg_json = await reg_resp.json()
    assert reg_json == {"success": True}
    await hass.async_block_till_done()

    assert "Re-register" not in caplog.text

    entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert entity is not None

    assert entity.attributes["device_class"] == "plug"
    assert entity.attributes["icon"] == "mdi:power-plug"
    assert entity.attributes["foo"] == "bar"
    assert entity.domain == "binary_sensor"
    assert entity.name == "Test 1 Is Charging"
    assert entity.state == "on"

    payload["data"]["state"] = False
    dupe_resp = await webhook_client.post(webhook_url, json=payload)

    assert dupe_resp.status == HTTPStatus.CREATED
    dupe_reg_json = await dupe_resp.json()
    assert dupe_reg_json == {"success": True}
    await hass.async_block_till_done()

    assert "Re-register" in caplog.text

    entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert entity is not None

    assert entity.attributes["device_class"] == "plug"
    assert entity.attributes["icon"] == "mdi:power-plug"
    assert entity.attributes["foo"] == "bar"
    assert entity.domain == "binary_sensor"
    assert entity.name == "Test 1 Is Charging"
    assert entity.state == "off"