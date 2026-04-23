async def test_reregister_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that we can add more info in re-registration."""
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

    entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entry.original_name == "Test 1 Battery State"
    assert entry.device_class is None
    assert entry.unit_of_measurement is None
    assert entry.entity_category is None
    assert entry.original_icon == "mdi:cellphone"
    assert entry.disabled_by is None

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "New Name",
                "state": 100,
                "type": "sensor",
                "unique_id": "abcd",
                "state_class": "measurement",
                "device_class": "battery",
                "entity_category": "diagnostic",
                "icon": "mdi:new-icon",
                "unit_of_measurement": "%",
                "disabled": True,
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entry.original_name == "Test 1 New Name"
    assert entry.device_class == "battery"
    assert entry.unit_of_measurement == "%"
    assert entry.entity_category == "diagnostic"
    assert entry.original_icon == "mdi:new-icon"
    assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "New Name",
                "type": "sensor",
                "unique_id": "abcd",
                "disabled": False,
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entry.disabled_by is None

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "New Name 2",
                "state": 100,
                "type": "sensor",
                "unique_id": "abcd",
                "state_class": None,
                "device_class": None,
                "entity_category": None,
                "icon": None,
                "unit_of_measurement": None,
            },
        },
    )

    assert reg_resp.status == HTTPStatus.CREATED
    entry = entity_registry.async_get("sensor.test_1_battery_state")
    assert entry.original_name == "Test 1 New Name 2"
    assert entry.device_class is None
    assert entry.unit_of_measurement is None
    assert entry.entity_category is None
    assert entry.original_icon is None