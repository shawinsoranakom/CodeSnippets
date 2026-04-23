async def test_register_sensor_no_state(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that sensors can be registered, when there is no (unknown) state."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": None,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None

    assert entity.domain == "sensor"
    assert entity.name == "Test 1 Battery State"
    assert entity.state == STATE_UNKNOWN

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Backup Battery State",
                "type": "sensor",
                "unique_id": "backup_battery_state",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_backup_battery_state")
    assert entity

    assert entity.domain == "sensor"
    assert entity.name == "Test 1 Backup Battery State"
    assert entity.state == STATE_UNKNOWN