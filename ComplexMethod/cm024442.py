async def test_pending_update_fallback_to_restore_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that restored state is used when no pending update exists."""
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
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None
    assert entity.state == "100"

    # Update to a new state
    await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "state": 75,
                    "type": "sensor",
                    "unique_id": "battery_state",
                }
            ],
        },
    )
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None
    assert entity.state == "75"

    # Reload without pending updates
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify restored state was used
    entity = hass.states.get("sensor.test_1_battery_state")
    assert entity is not None
    assert entity.state == "75"