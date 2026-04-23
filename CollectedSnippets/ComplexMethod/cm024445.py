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
                "name": "Is Charging",
                "state": None,
                "type": "binary_sensor",
                "unique_id": "is_charging",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert entity is not None

    assert entity.domain == "binary_sensor"
    assert entity.name == "Test 1 Is Charging"
    assert entity.state == STATE_UNKNOWN

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Backup Is Charging",
                "type": "binary_sensor",
                "unique_id": "backup_is_charging",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("binary_sensor.test_1_backup_is_charging")
    assert entity

    assert entity.domain == "binary_sensor"
    assert entity.name == "Test 1 Backup Is Charging"
    assert entity.state == STATE_UNKNOWN