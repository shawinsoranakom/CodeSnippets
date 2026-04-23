async def test_unique_id_migration_dupes(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    multisensor_6_state,
    client,
    integration,
) -> None:
    """Test we remove an entity when ."""
    entity_name = AIR_TEMPERATURE_SENSOR.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id_1 = (
        f"{client.driver.controller.home_id}.52.52-49-00-Air temperature-00"
    )
    entity_entry = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_1,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == AIR_TEMPERATURE_SENSOR
    assert entity_entry.unique_id == old_unique_id_1

    # Create entity RegistryEntry using b0 unique ID format
    old_unique_id_2 = (
        f"{client.driver.controller.home_id}.52.52-49-0-Air temperature-00-00"
    )
    entity_entry = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_2,
        suggested_object_id=f"{entity_name}_1",
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == f"{AIR_TEMPERATURE_SENSOR}_1"
    assert entity_entry.unique_id == old_unique_id_2

    # Add a ready node, unique ID should be migrated
    node = Node(client, copy.deepcopy(multisensor_6_state))
    event = {"node": node}

    client.driver.controller.emit("node added", event)
    await hass.async_block_till_done()

    # Check that new RegistryEntry is using new unique ID format
    entity_entry = entity_registry.async_get(AIR_TEMPERATURE_SENSOR)
    new_unique_id = f"{client.driver.controller.home_id}.52-49-0-Air temperature"
    assert entity_entry.unique_id == new_unique_id
    assert (
        entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id_1) is None
    )
    assert (
        entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id_2) is None
    )