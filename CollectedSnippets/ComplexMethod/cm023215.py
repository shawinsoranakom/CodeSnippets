async def test_get_actions(
    hass: HomeAssistant,
    client: Client,
    lock_schlage_be469: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we get the expected actions from a zwave_js node."""
    node = lock_schlage_be469
    driver = client.driver
    assert driver
    device = device_registry.async_get_device(identifiers={get_device_id(driver, node)})
    assert device
    binary_sensor = entity_registry.async_get(
        "binary_sensor.touchscreen_deadbolt_low_battery_level"
    )
    assert binary_sensor
    lock = entity_registry.async_get("lock.touchscreen_deadbolt")
    assert lock
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "clear_lock_usercode",
            "device_id": device.id,
            "entity_id": lock.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": DOMAIN,
            "type": "set_lock_usercode",
            "device_id": device.id,
            "entity_id": lock.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": DOMAIN,
            "type": "refresh_value",
            "device_id": device.id,
            "entity_id": binary_sensor.id,
            "metadata": {"secondary": True},
        },
        {
            "domain": DOMAIN,
            "type": "refresh_value",
            "device_id": device.id,
            "entity_id": lock.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": DOMAIN,
            "type": "set_value",
            "device_id": device.id,
            "metadata": {},
        },
        {
            "domain": DOMAIN,
            "type": "ping",
            "device_id": device.id,
            "metadata": {},
        },
        {
            "domain": DOMAIN,
            "type": "set_config_parameter",
            "device_id": device.id,
            "endpoint": 0,
            "parameter": 3,
            "bitmask": None,
            "subtype": "3 (Beeper) on endpoint 0",
            "metadata": {},
        },
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device.id
    )
    for action in expected_actions:
        assert action in actions

    # Test that we don't return actions for a controller node
    device = device_registry.async_get_device(
        identifiers={get_device_id(driver, client.driver.controller.nodes[1])}
    )
    assert device
    assert (
        await async_get_device_automations(hass, DeviceAutomationType.ACTION, device.id)
        == []
    )