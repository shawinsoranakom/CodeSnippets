async def test_sensor_migration(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
    unique_id: str,
    unit_system: UnitSystem,
    state_unit: UnitOfTemperature,
    state1: str,
    state2: str,
) -> None:
    """Test migration to RestoreSensor."""
    hass.config.units = unit_system

    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "attributes": {"foo": "bar"},
                "device_class": "temperature",
                "icon": "mdi:battery",
                "name": "Battery Temperature",
                "state": 100,
                "type": "sensor",
                "entity_category": "diagnostic",
                "unique_id": unique_id,
                "state_class": "measurement",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    json = await reg_resp.json()
    assert json == {"success": True}
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_temperature")
    assert entity is not None

    assert entity.attributes["device_class"] == "temperature"
    assert entity.attributes["icon"] == "mdi:battery"
    # unit of temperature sensor is automatically converted to the system UoM
    assert entity.attributes["unit_of_measurement"] == state_unit
    assert entity.attributes["foo"] == "bar"
    assert entity.attributes["state_class"] == "measurement"
    assert entity.domain == "sensor"
    assert entity.name == "Test 1 Battery Temperature"
    assert float(entity.state) == state1

    # Reload to verify state is restored
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    unloaded_entity = hass.states.get("sensor.test_1_battery_temperature")
    assert unloaded_entity.state == STATE_UNAVAILABLE

    # Simulate migration to RestoreSensor
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_extra_data",
        return_value=None,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    restored_entity = hass.states.get("sensor.test_1_battery_temperature")
    assert restored_entity.state == "unknown"
    assert restored_entity.attributes == entity.attributes

    # Test unit conversion is working
    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": unique_id,
                },
            ],
        },
    )

    assert update_resp.status == HTTPStatus.OK

    updated_entity = hass.states.get("sensor.test_1_battery_temperature")
    assert round(float(updated_entity.state), 0) == state2
    assert "foo" not in updated_entity.attributes