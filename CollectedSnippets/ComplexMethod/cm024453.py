async def test_recreate_correct_from_entity_registry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that sensors can be re-created from entity registry."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "device_class": "battery",
                "icon": "mdi:battery",
                "name": "Battery State",
                "state": 100,
                "type": "sensor",
                "unique_id": "battery_state",
                "unit_of_measurement": PERCENTAGE,
                "state_class": "measurement",
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

    entity = hass.states.get("sensor.test_1_battery_state")

    assert entity is not None
    entity_entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entity_entry is not None

    assert entity_entry.capabilities == {
        "state_class": "measurement",
    }

    entry = hass.config_entries.async_entries("mobile_app")[1]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_1_battery_state").state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entity_entry is not None
    assert hass.states.get("sensor.test_1_battery_state") is not None

    assert entity_entry.capabilities == {
        "state_class": "measurement",
    }