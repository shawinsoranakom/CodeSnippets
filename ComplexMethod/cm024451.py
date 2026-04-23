async def test_update_sensor_no_state(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that sensors can be updated, when there is no (unknown) state."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 100,
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
    assert entity.state == "100"

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [{"state": None, "type": "sensor", "unique_id": "battery_state"}],
        },
    )

    assert update_resp.status == HTTPStatus.OK

    json = await update_resp.json()
    assert json == {"battery_state": {"success": True}}

    updated_entity = hass.states.get("sensor.test_1_battery_state")
    assert updated_entity.state == STATE_UNKNOWN