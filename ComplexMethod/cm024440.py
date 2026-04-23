async def test_sending_sensor_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that we can register and send sensor state as number and None."""
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
                "unique_id": "abcd",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery Health",
                "state": "good",
                "type": "sensor",
                "unique_id": "health-id",
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED

    entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entry.original_name == "Test 1 Battery State"
    assert entry.device_class is None
    assert entry.unit_of_measurement is None
    assert entry.entity_category is None
    assert entry.original_icon == "mdi:cellphone"
    assert entry.disabled_by is None

    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_1_battery_state")
    assert state is not None
    assert state.state == "100"

    state = hass.states.get("sensor.test_1_battery_health")
    assert state is not None
    assert state.state == "good"

    # Now with a list.
    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "state": 50.0000,
                    "type": "sensor",
                    "unique_id": "abcd",
                },
                {
                    "state": "okay-ish",
                    "type": "sensor",
                    "unique_id": "health-id",
                },
            ],
        },
    )

    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_1_battery_state")
    assert state is not None
    assert state.state == "50.0"

    state = hass.states.get("sensor.test_1_battery_health")
    assert state is not None
    assert state.state == "okay-ish"