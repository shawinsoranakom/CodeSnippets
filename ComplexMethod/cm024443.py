async def test_sensor(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that sensors can be registered and updated."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
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
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert entity is not None

    assert entity.attributes["device_class"] == "plug"
    assert entity.attributes["icon"] == "mdi:power-plug"
    assert entity.attributes["foo"] == "bar"
    assert entity.domain == "binary_sensor"
    assert entity.name == "Test 1 Is Charging"
    assert entity.state == "on"

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": False,
                    "type": "binary_sensor",
                    "unique_id": "is_charging",
                },
                # This invalid data should not invalidate whole request
                {
                    "type": "binary_sensor",
                    "unique_id": "invalid_state",
                    "invalid": "data",
                },
            ],
        },
    )

    assert update_resp.status == HTTPStatus.OK

    json = await update_resp.json()
    assert json["invalid_state"]["success"] is False

    updated_entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert updated_entity.state == "off"
    assert "foo" not in updated_entity.attributes

    assert len(device_registry.devices) == len(create_registrations)

    # Reload to verify state is restored
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    unloaded_entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert unloaded_entity.state == "unavailable"

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    restored_entity = hass.states.get("binary_sensor.test_1_is_charging")
    assert restored_entity.state == updated_entity.state
    assert restored_entity.attributes == updated_entity.attributes