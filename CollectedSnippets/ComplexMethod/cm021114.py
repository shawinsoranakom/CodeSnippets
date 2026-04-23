async def test_select_setup_camera_none(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    camera: Camera,
) -> None:
    """Test select entity setup for camera devices (no features)."""

    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.SELECT, 2, 2)

    expected_values = ("always", "auto", "Default Message (Welcome)")

    for index, description in enumerate(CAMERA_SELECTS):
        if index == 2:
            return

        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.SELECT, camera, description
        )

        entity = entity_registry.async_get(entity_id)
        assert entity
        assert entity.unique_id == unique_id

        state = hass.states.get(entity_id)
        assert state
        assert state.state == expected_values[index]
        assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION