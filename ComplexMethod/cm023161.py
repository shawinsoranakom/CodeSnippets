async def test_skip_old_entity_migration_for_multiple(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    hank_binary_switch_state,
    client,
    integration,
) -> None:
    """Test that multiple entities of the same value but on a different endpoint get skipped."""
    node = Node(client, copy.deepcopy(hank_binary_switch_state))
    driver = client.driver
    assert driver

    device = device_registry.async_get_or_create(
        config_entry_id=integration.entry_id,
        identifiers={get_device_id(driver, node)},
        manufacturer=hank_binary_switch_state["deviceConfig"]["manufacturer"],
        model=hank_binary_switch_state["deviceConfig"]["label"],
    )

    SENSOR_NAME = "sensor.smart_plug_with_two_usb_ports_value_electric_consumed"
    entity_name = SENSOR_NAME.split(".")[1]

    # Create two entity entrrys using different endpoints
    old_unique_id_1 = f"{driver.controller.home_id}.32-50-1-value-66049"
    entity_entry = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_1,
        suggested_object_id=f"{entity_name}_1",
        config_entry=integration,
        original_name=f"{entity_name}_1",
        device_id=device.id,
    )
    assert entity_entry.entity_id == f"{SENSOR_NAME}_1"
    assert entity_entry.unique_id == old_unique_id_1

    # Create two entity entrrys using different endpoints
    old_unique_id_2 = f"{driver.controller.home_id}.32-50-2-value-66049"
    entity_entry = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_2,
        suggested_object_id=f"{entity_name}_2",
        config_entry=integration,
        original_name=f"{entity_name}_2",
        device_id=device.id,
    )
    assert entity_entry.entity_id == f"{SENSOR_NAME}_2"
    assert entity_entry.unique_id == old_unique_id_2
    # Add a ready node, unique ID should be migrated
    event = {"node": node}
    driver.controller.emit("node added", event)
    await hass.async_block_till_done()

    # Check that new RegistryEntry is created using new unique ID format
    entity_entry = entity_registry.async_get(SENSOR_NAME)
    new_unique_id = f"{driver.controller.home_id}.32-50-0-value-66049"
    assert entity_entry.unique_id == new_unique_id

    # Check that the old entities stuck around because we skipped the migration step
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id_1)
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id_2)