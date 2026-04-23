async def test_pending_update_with_attributes(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that pending updates preserve all attributes."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    # Register a sensor
    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 100,
                "type": "sensor",
                "unique_id": "battery_state",
                "attributes": {"charging": True, "voltage": 4.2},
                "icon": "mdi:battery-charging",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    await hass.async_block_till_done()

    # Disable the entity
    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    # Send update with different attributes while disabled
    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 50,
                "type": "sensor",
                "unique_id": "battery_state",
                "attributes": {"charging": False, "voltage": 3.7},
                "icon": "mdi:battery-50",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    await hass.async_block_till_done()

    # Re-enable the entity
    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)

    # Reload the config entry
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify all attributes were applied
    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None
    assert entity.state == "50"
    assert entity.attributes["charging"] is False
    assert entity.attributes["voltage"] == 3.7
    assert entity.attributes["icon"] == "mdi:battery-50"