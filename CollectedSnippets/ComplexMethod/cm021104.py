async def test_binary_sensor_setup_camera_all(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
) -> None:
    """Test binary_sensor entity setup for camera devices (all features)."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 9, 6)

    description = EVENT_SENSORS[0]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    # Is Dark
    description = CAMERA_SENSORS[0]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    # Motion
    description = EVENT_SENSORS[1]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION