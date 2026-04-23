async def test_sensor_nvr_missing_values(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, ufp: MockUFPFixture
) -> None:
    """Test NVR sensor sensors if no data available."""

    reset_objects(ufp.api.bootstrap)
    nvr: NVR = ufp.api.bootstrap.nvr
    nvr.system_info.memory.available = None
    nvr.system_info.memory.total = None
    nvr.up_since = None
    nvr.storage_stats.capacity = None

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    assert_entity_counts(hass, Platform.SENSOR, 12, 9)

    # Uptime
    description = get_sensor_by_key(NVR_SENSORS, "uptime")
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.SENSOR, nvr, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    # Recording capacity
    description = get_sensor_by_key(NVR_SENSORS, "record_capacity")
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.SENSOR, nvr, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "0"
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    # Memory utilization
    description = get_sensor_by_key(NVR_DISABLED_SENSORS, "memory_utilization")
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.SENSOR, nvr, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.disabled is True
    assert entity.unique_id == unique_id

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION