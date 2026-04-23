async def test_switch_setup_camera_all(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    doorbell: Camera,
) -> None:
    """Test switch entity setup for camera devices (all enabled feature flags)."""

    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    for description in CAMERA_SWITCHES_BASIC:
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.SWITCH, doorbell, description
        )

        entity = entity_registry.async_get(entity_id)
        assert entity
        assert entity.unique_id == unique_id

        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_OFF
        assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    description = CAMERA_SWITCHES[0]

    unique_id = f"{doorbell.mac}_{description.key}"
    entity_id = f"switch.test_camera_{description.translation_key}"

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.disabled is True
    assert entity.unique_id == unique_id

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION