async def test_updating_disabled_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that sensors return error if disabled in instance."""
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

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_state",
                },
            ],
        },
    )

    assert update_resp.status == HTTPStatus.OK

    json = await update_resp.json()
    assert json["battery_state"]["success"] is True
    assert "is_disabled" not in json["battery_state"]

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_state",
                },
            ],
        },
    )

    assert update_resp.status == HTTPStatus.OK

    json = await update_resp.json()
    assert json["battery_state"]["success"] is True
    assert json["battery_state"]["is_disabled"] is True